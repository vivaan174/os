/*
 * Dynamic Resource Allocator - Full-featured C Implementation with Web Server
 * 
 * Complete system resource monitoring and dynamic allocation with:
 * - Full process tracking table (up to 500 processes)
 * - Real-time system metrics collection
 * - Proper HTTP/JSON request and response handling
 * - Workload simulation (CPU/Memory/I/O stress testing)
 * - Adaptive resource control with process suspension/resumption
 * 
 * Compile: gcc -o allocator allocator.c -lpthread -lm
 * Run: ./allocator
 * Access: http://localhost:7860
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <signal.h>
#include <dirent.h>
#include <fcntl.h>
#include <ctype.h>

#define MAX_PROCESSES 500
#define MAX_HISTORY 300
#define BUFFER_SIZE 16384
#define MAX_JSON_SIZE 65536
#define PORT 7860

/* ============================================================================
 * DATA STRUCTURES
 * ============================================================================ */

typedef enum {
    PRIORITY_CRITICAL = 5,
    PRIORITY_HIGH = 4,
    PRIORITY_NORMAL = 3,
    PRIORITY_LOW = 2,
    PRIORITY_BACKGROUND = 1
} ProcessPriority;

typedef enum {
    STRATEGY_EQUAL = 0,
    STRATEGY_PRIORITY = 1,
    STRATEGY_PERFORMANCE = 2,
    STRATEGY_DEMAND = 3
} AllocationStrategy;

typedef struct {
    double cpu_percent;
    double memory_percent;
    int cpu_count;
    double memory_used_mb;
    double memory_total_mb;
    double memory_available_mb;
    int process_count;
    time_t timestamp;
} SystemMetrics;

// COMPLETE PROCESS TRACKING TABLE WITH PER-PROCESS METRICS
typedef struct {
    int pid;
    char name[256];
    ProcessPriority priority;
    double cpu_percent;           // Per-process CPU usage
    double memory_percent;         // Per-process memory usage
    int active;                   // Is process still running?
    time_t registered_time;       // When was it registered?
} TrackedProcess;

typedef struct {
    SystemMetrics metrics[MAX_HISTORY];
    int history_count;
    int running;
    time_t start_time;
    AllocationStrategy strategy;
    
    // FULL PROCESS TRACKING TABLE (Main change from old version)
    TrackedProcess tracked[MAX_PROCESSES];
    int tracked_count;
    
    // Workload state
    int active_workloads;
    
    // Thread management
    pthread_mutex_t lock;
    pthread_t monitor_thread;
    pthread_t optimizer_thread;
    pthread_t server_thread;
    int shutdown_flag;
} SystemState;

/* ============================================================================
 * GLOBAL STATE
 * ============================================================================ */

SystemState state = {0};

/* ============================================================================
 * UTILITY FUNCTIONS
 * ============================================================================ */

const char* priority_to_string(ProcessPriority p) {
    switch(p) {
        case PRIORITY_CRITICAL: return "CRITICAL";
        case PRIORITY_HIGH: return "HIGH";
        case PRIORITY_NORMAL: return "NORMAL";
        case PRIORITY_LOW: return "LOW";
        case PRIORITY_BACKGROUND: return "BACKGROUND";
        default: return "UNKNOWN";
    }
}

ProcessPriority string_to_priority(const char *str) {
    if (!str) return PRIORITY_NORMAL;
    if (strcmp(str, "CRITICAL") == 0 || strcmp(str, "5") == 0) return PRIORITY_CRITICAL;
    if (strcmp(str, "HIGH") == 0 || strcmp(str, "4") == 0) return PRIORITY_HIGH;
    if (strcmp(str, "NORMAL") == 0 || strcmp(str, "3") == 0) return PRIORITY_NORMAL;
    if (strcmp(str, "LOW") == 0 || strcmp(str, "2") == 0) return PRIORITY_LOW;
    if (strcmp(str, "BACKGROUND") == 0 || strcmp(str, "1") == 0) return PRIORITY_BACKGROUND;
    return PRIORITY_NORMAL;
}

const char* strategy_to_string(AllocationStrategy s) {
    switch(s) {
        case STRATEGY_EQUAL: return "equal";
        case STRATEGY_PRIORITY: return "priority";
        case STRATEGY_PERFORMANCE: return "performance";
        case STRATEGY_DEMAND: return "demand";
        default: return "unknown";
    }
}

// JSON PARSING HELPERS FOR POST REQUEST BODIES
int json_get_int(const char *json, const char *key) {
    if (!json || !key) return 0;
    char search[256];
    snprintf(search, sizeof(search), "\"%s\"", key);
    
    const char *pos = strstr(json, search);
    if (!pos) return 0;
    
    pos = strchr(pos, ':');
    if (!pos) return 0;
    pos++;
    
    while (*pos && isspace(*pos)) pos++;
    
    int value = 0;
    sscanf(pos, "%d", &value);
    return value;
}

char* json_get_string(const char *json, const char *key, char *out, int max_len) {
    if (!json || !key || !out) {
        if (out) out[0] = '\0';
        return out;
    }
    
    char search[256];
    snprintf(search, sizeof(search), "\"%s\"", key);
    
    const char *pos = strstr(json, search);
    if (!pos) {
        out[0] = '\0';
        return out;
    }
    
    pos = strchr(pos, ':');
    if (!pos) {
        out[0] = '\0';
        return out;
    }
    pos++;
    
    while (*pos && isspace(*pos)) pos++;
    
    if (*pos == '"') {
        pos++;
        int i = 0;
        while (*pos && *pos != '"' && i < max_len - 1) {
            out[i++] = *pos++;
        }
        out[i] = '\0';
    } else {
        out[0] = '\0';
    }
    
    return out;
}

/* ============================================================================
 * SYSTEM MONITORING
 * ============================================================================ */

double get_cpu_usage() {
    FILE *fp = fopen("/proc/stat", "r");
    if (!fp) return 0.0;
    
    static unsigned long prev_idle = 0, prev_total = 0;
    unsigned long user, nice, system, idle, iowait, irq, softirq;
    
    if (fscanf(fp, "cpu %lu %lu %lu %lu %lu %lu %lu", &user, &nice, &system, &idle, &iowait, &irq, &softirq) != 7) {
        // Handle parse error if necessary
    }
    fclose(fp);
    
    unsigned long total = user + nice + system + idle + iowait + irq + softirq;
    unsigned long total_delta = total - prev_total;
    unsigned long idle_delta = idle - prev_idle;
    
    prev_total = total;
    prev_idle = idle;
    
    if (total_delta == 0) return 0.0;
    double cpu_percent = 100.0 * (double)(total_delta - idle_delta) / total_delta;
    return cpu_percent > 100.0 ? 100.0 : cpu_percent;
}

double get_memory_usage(double *used_mb, double *total_mb, double *available_mb) {
    FILE *fp = fopen("/proc/meminfo", "r");
    if (!fp) return 0.0;
    
    double mem_total = 0, mem_free = 0, mem_available = 0;
    char line[256];
    
    while (fgets(line, sizeof(line), fp)) {
        if (sscanf(line, "MemTotal: %lf", &mem_total) == 1) mem_total *= 1024;
        else if (sscanf(line, "MemFree: %lf", &mem_free) == 1) mem_free *= 1024;
        else if (sscanf(line, "MemAvailable: %lf", &mem_available) == 1) mem_available *= 1024;
    }
    fclose(fp);
    
    *total_mb = mem_total / (1024 * 1024);
    *available_mb = mem_available / (1024 * 1024);
    *used_mb = (*total_mb) - (*available_mb);
    
    return mem_total > 0 ? (100.0 * (mem_total - mem_free) / mem_total) : 0.0;
}

int count_processes() {
    DIR *dir = opendir("/proc");
    if (!dir) return 0;
    
    int count = 0;
    struct dirent *entry;
    
    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type == DT_DIR && atoi(entry->d_name) > 0) {
            count++;
        }
    }
    closedir(dir);
    return count;
}

int get_cpu_count() {
    FILE *fp = fopen("/proc/cpuinfo", "r");
    if (!fp) return 1;
    
    int count = 0;
    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "processor", 9) == 0) count++;
    }
    fclose(fp);
    return count > 0 ? count : 1;
}

// PER-PROCESS METRICS COLLECTION
double get_process_cpu_percent(int pid) {
    char path[256];
    snprintf(path, sizeof(path), "/proc/%d/stat", pid);
    FILE *fp = fopen(path, "r");
    if (!fp) return 0.0;
    
    unsigned long utime = 0, stime = 0;
    for (int i = 1; i <= 13; i++) {
        if (fscanf(fp, "%*s") == EOF) break;
    }
    if (fscanf(fp, "%lu %lu", &utime, &stime) != 2) {
        utime = 0; stime = 0;
    }
    fclose(fp);
    
    double cpu_percent = ((double)(utime + stime) / 100.0);
    return cpu_percent > 100.0 ? 100.0 : (cpu_percent < 0.0 ? 0.0 : cpu_percent);
}

double get_process_memory_percent(int pid) {
    char path[256];
    snprintf(path, sizeof(path), "/proc/%d/status", pid);
    FILE *fp = fopen(path, "r");
    if (!fp) return 0.0;
    
    unsigned long vm_rss = 0;
    char line[256];
    
    while (fgets(line, sizeof(line), fp)) {
        if (sscanf(line, "VmRSS: %lu", &vm_rss) == 1) {
            break;
        }
    }
    fclose(fp);
    
    double total_mb = 0, used_mb = 0, available_mb = 0;
    get_memory_usage(&used_mb, &total_mb, &available_mb);
    
    double rss_mb = vm_rss / 1024.0;
    double mem_percent = (rss_mb / total_mb) * 100.0;
    return mem_percent > 100.0 ? 100.0 : (mem_percent < 0.0 ? 0.0 : mem_percent);
}

void collect_metrics() {
    SystemMetrics m;
    m.timestamp = time(NULL);
    m.cpu_percent = get_cpu_usage();
    m.cpu_count = get_cpu_count();
    m.memory_percent = get_memory_usage(&m.memory_used_mb, &m.memory_total_mb, &m.memory_available_mb);
    m.process_count = count_processes();
    
    pthread_mutex_lock(&state.lock);
    
    if (state.history_count < MAX_HISTORY) {
        state.metrics[state.history_count++] = m;
    } else {
        for (int i = 0; i < MAX_HISTORY - 1; i++) {
            state.metrics[i] = state.metrics[i + 1];
        }
        state.metrics[MAX_HISTORY - 1] = m;
    }
    
    // UPDATE PER-PROCESS METRICS
    for (int i = 0; i < state.tracked_count; i++) {
        if (state.tracked[i].active) {
            state.tracked[i].cpu_percent = get_process_cpu_percent(state.tracked[i].pid);
            state.tracked[i].memory_percent = get_process_memory_percent(state.tracked[i].pid);
            
            // Check if process still exists
            char proc_path[256];
            snprintf(proc_path, sizeof(proc_path), "/proc/%d", state.tracked[i].pid);
            if (access(proc_path, F_OK) == -1) {
                state.tracked[i].active = 0;
            }
        }
    }
    
    pthread_mutex_unlock(&state.lock);
}

/* ============================================================================
 * RESOURCE MANAGER
 * ============================================================================ */

int register_process(int pid, const char *name, ProcessPriority priority) {
    // Verify process exists
    char path[256];
    snprintf(path, sizeof(path), "/proc/%d", pid);
    if (access(path, F_OK) == -1) return 0;
    
    pthread_mutex_lock(&state.lock);
    
    // Check if already registered
    for (int i = 0; i < state.tracked_count; i++) {
        if (state.tracked[i].pid == pid && state.tracked[i].active) {
            pthread_mutex_unlock(&state.lock);
            return 0;  // Already registered
        }
    }
    
    // Add to tracking table
    if (state.tracked_count < MAX_PROCESSES) {
        state.tracked[state.tracked_count].pid = pid;
        strncpy(state.tracked[state.tracked_count].name, name, sizeof(state.tracked[state.tracked_count].name) - 1);
        state.tracked[state.tracked_count].priority = priority;
        state.tracked[state.tracked_count].active = 1;
        state.tracked[state.tracked_count].registered_time = time(NULL);
        state.tracked[state.tracked_count].cpu_percent = 0.0;
        state.tracked[state.tracked_count].memory_percent = 0.0;
        state.tracked_count++;
        pthread_mutex_unlock(&state.lock);
        return 1;
    }
    
    pthread_mutex_unlock(&state.lock);
    return 0;
}

int unregister_process(int pid) {
    pthread_mutex_lock(&state.lock);
    
    for (int i = 0; i < state.tracked_count; i++) {
        if (state.tracked[i].pid == pid) {
            state.tracked[i].active = 0;
            pthread_mutex_unlock(&state.lock);
            return 1;
        }
    }
    
    pthread_mutex_unlock(&state.lock);
    return 0;
}

int set_priority(int pid, ProcessPriority priority) {
    pthread_mutex_lock(&state.lock);
    
    for (int i = 0; i < state.tracked_count; i++) {
        if (state.tracked[i].pid == pid && state.tracked[i].active) {
            state.tracked[i].priority = priority;
            pthread_mutex_unlock(&state.lock);
            return 1;
        }
    }
    
    pthread_mutex_unlock(&state.lock);
    return 0;
}

int get_tracked_count() {
    int count = 0;
    for (int i = 0; i < state.tracked_count; i++) {
        if (state.tracked[i].active) count++;
    }
    return count;
}

/* ============================================================================
 * PERFORMANCE OPTIMIZER
 * ============================================================================ */

void apply_adaptive_control() {
    if (state.history_count == 0) return;
    
    SystemMetrics *latest = &state.metrics[state.history_count - 1];
    
    pthread_mutex_lock(&state.lock);
    
    if (latest->cpu_percent > 85 || latest->memory_percent > 90) {
        // Suspend low-priority processes
        for (int i = 0; i < state.tracked_count; i++) {
            if (state.tracked[i].priority <= PRIORITY_LOW) {
                kill(state.tracked[i].pid, SIGSTOP);
            }
        }
    } else {
        // Resume suspended processes if resources available
        for (int i = 0; i < state.tracked_count; i++) {
            if (state.tracked[i].priority <= PRIORITY_LOW) {
                kill(state.tracked[i].pid, SIGCONT);
            }
        }
    }
    
    pthread_mutex_unlock(&state.lock);
}

/* ============================================================================
 * WORKLOAD SIMULATOR
 * ============================================================================ */

void* cpu_workload_thread(void *arg) {
    int intensity = *(int*)arg;
    free(arg);
    
    int duration = 30;
    time_t end = time(NULL) + duration;
    
    while (time(NULL) < end && !state.shutdown_flag) {
        volatile double sum = 0;
        for (int i = 0; i < (100000 * intensity / 100); i++) {
            sum += i * i;
        }
    }
    
    state.active_workloads--;
    return NULL;
}

void* memory_workload_thread(void *arg) {
    int size_mb = *(int*)arg;
    free(arg);
    
    int duration = 30;
    
    void *buffer = malloc(size_mb * 1024 * 1024);
    if (buffer) {
        memset(buffer, 0xAA, size_mb * 1024 * 1024);
        sleep(duration);
        free(buffer);
    }
    
    state.active_workloads--;
    return NULL;
}

void* io_workload_thread(void *arg) {
    int num_files = *(int*)arg;
    free(arg);
    
    int duration = 30;
    time_t end = time(NULL) + duration;
    
    while (time(NULL) < end && !state.shutdown_flag) {
        for (int i = 0; i < num_files; i++) {
            char filename[256];
            snprintf(filename, sizeof(filename), "/tmp/test_io_%d.tmp", i);
            FILE *fp = fopen(filename, "w");
            if (fp) {
                for (int j = 0; j < 100; j++) {
                    fprintf(fp, "XXXXXXXXXX");
                }
                fclose(fp);
                unlink(filename);
            }
        }
    }
    
    state.active_workloads--;
    return NULL;
}

/* ============================================================================
 * HTTP SERVER - PROPER REQUEST/RESPONSE HANDLING
 * ============================================================================ */

typedef struct {
    char method[16];
    char path[256];
    char protocol[16];
    char *body;
    int body_len;
} HttpRequest;

int parse_http_request(const char *buffer, int len, HttpRequest *req) {
    memset(req, 0, sizeof(HttpRequest));
    
    // Parse request line
    sscanf(buffer, "%s %s %s", req->method, req->path, req->protocol);
    
    // Find body (after \r\n\r\n)
    const char *body_start = strstr(buffer, "\r\n\r\n");
    if (body_start) {
        body_start += 4;
        req->body = (char*)body_start;
        req->body_len = len - (body_start - buffer);
    }
    
    return 1;
}

void send_http_response(int client_sock, int status_code, const char *content_type, const char *body) {
    char response[MAX_JSON_SIZE * 2];
    
    snprintf(response, sizeof(response),
        "HTTP/1.1 %d OK\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %zu\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Connection: close\r\n"
        "\r\n"
        "%s",
        status_code,
        content_type,
        strlen(body),
        body
    );
    
    send(client_sock, response, strlen(response), 0);
}

char* get_status_json() {
    static char buffer[2048];
    
    pthread_mutex_lock(&state.lock);
    
    SystemMetrics *latest = state.history_count > 0 ? &state.metrics[state.history_count - 1] : NULL;
    time_t uptime = (time(NULL) - state.start_time);
    int tracked = get_tracked_count();
    
    snprintf(buffer, sizeof(buffer),
        "{"
        "\"running\":%d,"
        "\"uptime_seconds\":%ld,"
        "\"strategy\":\"%s\","
        "\"tracked_programs\":%d,"
        "\"cpu_percent\":%.1f,"
        "\"memory_percent\":%.1f,"
        "\"cpu_count\":%d,"
        "\"process_count\":%d,"
        "\"active_workloads\":%d"
        "}",
        state.running,
        uptime,
        strategy_to_string(state.strategy),
        tracked,
        latest ? latest->cpu_percent : 0.0,
        latest ? latest->memory_percent : 0.0,
        latest ? latest->cpu_count : 1,
        latest ? latest->process_count : 0,
        state.active_workloads
    );
    
    pthread_mutex_unlock(&state.lock);
    return buffer;
}

char* get_tracked_json() {
    static char buffer[MAX_JSON_SIZE];
    
    pthread_mutex_lock(&state.lock);
    
    strcpy(buffer, "{\"tracked\":[");
    int first = 1;
    
    for (int i = 0; i < state.tracked_count; i++) {
        if (state.tracked[i].active) {
            if (!first) strcat(buffer, ",");
            
            char proc_str[512];
            snprintf(proc_str, sizeof(proc_str),
                "{\"pid\":%d,\"name\":\"%s\",\"priority\":\"%s\",\"cpu\":%.1f,\"memory\":%.1f}",
                state.tracked[i].pid,
                state.tracked[i].name,
                priority_to_string(state.tracked[i].priority),
                state.tracked[i].cpu_percent,
                state.tracked[i].memory_percent
            );
            strcat(buffer, proc_str);
            first = 0;
        }
    }
    
    strcat(buffer, "]}");
    pthread_mutex_unlock(&state.lock);
    return buffer;
}


char* get_available_pids_text() {
    static char buffer[MAX_JSON_SIZE];
    strcpy(buffer, "📋 AVAILABLE PROCESSES\n==================================================\n(Current PID: ");
    char pid_str[32];
    snprintf(pid_str, sizeof(pid_str), "%d)\n\n", getpid());
    strcat(buffer, pid_str);
    
    DIR *dir = opendir("/proc");
    if (!dir) {
        strcat(buffer, "❌ No processes found\n");
        return buffer;
    }
    
    int total_count = 0;
    int added_count = 0;
    
    struct dirent *entry;
    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type == DT_DIR && isdigit(entry->d_name[0])) {
            total_count++;
            if (added_count < 100) {
                int pid = atoi(entry->d_name);
                char path[256];
                snprintf(path, sizeof(path), "/proc/%d/comm", pid);
                FILE *fp = fopen(path, "r");
                if (fp) {
                    char name[256] = {0};
                    if (fgets(name, sizeof(name), fp)) {
                        name[strcspn(name, "\n")] = 0;
                        char line[512];
                        snprintf(line, sizeof(line), "  PID: %6d - %s\n", pid, name);
                        if (strlen(buffer) + strlen(line) < sizeof(buffer) - 200) {
                            strcat(buffer, line);
                            added_count++;
                        }
                    }
                    fclose(fp);
                }
            }
        }
    }
    closedir(dir);
    
    char summary[128];
    snprintf(summary, sizeof(summary), "\n📊 Showing %d of %d Total Processes\n\n💡 Copy a PID from above and paste in Register field\n", added_count, total_count);
    strcat(buffer, summary);
    
    return buffer;
}

char* get_report_text() {
    static char buffer[MAX_JSON_SIZE];
    buffer[0] = '\0';
    
    pthread_mutex_lock(&state.lock);
    SystemMetrics *latest = state.history_count > 0 ? &state.metrics[state.history_count - 1] : NULL;
    int tracked = get_tracked_count();
    time_t uptime = state.start_time ? (time(NULL) - state.start_time) : 0;
    
    char tmp[1024];
    
    strcat(buffer, "📈 COMPREHENSIVE PERFORMANCE REPORT\n");
    strcat(buffer, "======================================================================\n\n");
    
    strcat(buffer, "🖥️  SYSTEM STATUS\n");
    strcat(buffer, "----------------------------------------------------------------------\n");
    snprintf(tmp, sizeof(tmp), "Status: %s\n", state.running ? "ACTIVE 🟢" : "INACTIVE 🔴");
    strcat(buffer, tmp);
    snprintf(tmp, sizeof(tmp), "Strategy: %s\n", strategy_to_string(state.strategy));
    strcat(buffer, tmp);
    
    int mins = uptime / 60;
    int secs = uptime % 60;
    snprintf(tmp, sizeof(tmp), "Uptime: %dm %ds\n", mins, secs);
    strcat(buffer, tmp);
    snprintf(tmp, sizeof(tmp), "Active Workloads: %d\n\n", state.active_workloads);
    strcat(buffer, tmp);
    
    if (latest) {
        strcat(buffer, "📊 REAL-TIME METRICS\n");
        strcat(buffer, "----------------------------------------------------------------------\n");
        snprintf(tmp, sizeof(tmp), "CPU Usage: %.1f%% (Cores: %d)\n", latest->cpu_percent, latest->cpu_count);
        strcat(buffer, tmp);
        snprintf(tmp, sizeof(tmp), "Memory: %.1f%% (%.0fMB used / %.0fMB total)\n", latest->memory_percent, latest->memory_used_mb, latest->memory_total_mb);
        strcat(buffer, tmp);
        snprintf(tmp, sizeof(tmp), "Available RAM: %.0fMB\n", latest->memory_available_mb);
        strcat(buffer, tmp);
        snprintf(tmp, sizeof(tmp), "Total Processes: %d\n\n", latest->process_count);
        strcat(buffer, tmp);
    }
    
    strcat(buffer, "📋 TRACKED PROCESSES\n");
    strcat(buffer, "----------------------------------------------------------------------\n");
    snprintf(tmp, sizeof(tmp), "Monitored: %d processes\n", tracked);
    strcat(buffer, tmp);
    
    if (tracked > 0) {
        for (int i = 0; i < state.tracked_count; i++) {
            if (state.tracked[i].active) {
                snprintf(tmp, sizeof(tmp), "  🟢 %s (PID: %d) | Priority: %s | CPU: %.1f%% | Mem: %.1f%%\n", 
                    state.tracked[i].name, state.tracked[i].pid, 
                    priority_to_string(state.tracked[i].priority), 
                    state.tracked[i].cpu_percent, state.tracked[i].memory_percent);
                strcat(buffer, tmp);
            }
        }
    } else {
        strcat(buffer, "  (No processes being tracked)\n");
    }
    strcat(buffer, "\n");
    
    strcat(buffer, "💡 SMART RECOMMENDATIONS\n");
    strcat(buffer, "----------------------------------------------------------------------\n");
    
    int recommendations = 0;
    if (latest) {
        if (latest->cpu_percent > 80) {
            snprintf(tmp, sizeof(tmp), "  ⚠️  HIGH CPU (%.1f%%) - Consider reducing workload or prioritizing critical tasks\n", latest->cpu_percent);
            strcat(buffer, tmp);
            recommendations++;
        }
        if (latest->memory_percent > 85) {
            snprintf(tmp, sizeof(tmp), "  ⚠️  HIGH MEMORY (%.1f%%) - Close unnecessary applications\n", latest->memory_percent);
            strcat(buffer, tmp);
            recommendations++;
        }
        if (latest->process_count > 400) {
            snprintf(tmp, sizeof(tmp), "  ⚠️  MANY PROCESSES (%d) - System getting crowded, may impact performance\n", latest->process_count);
            strcat(buffer, tmp);
            recommendations++;
        }
    }
    if (recommendations == 0) {
        strcat(buffer, "  ✅ System running optimally - All metrics within normal range\n");
    }
    
    strcat(buffer, "\n======================================================================\n");
    
    pthread_mutex_unlock(&state.lock);
    return buffer;
}

char* get_html_page() {

        static const char html[] = 
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        "  <title>Dynamic Resource Allocator</title>\n"
        "  <meta charset=\"UTF-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "  <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>\n"
        "  <style>\n"
        "    body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f0f4f8; color: #333; }\n"
        "    .container { max-width: 1200px; margin: 0 auto; }\n"
        "    h1 { color: #0056b3; border-bottom: 2px solid #cce5ff; padding-bottom: 10px; margin-bottom: 30px; font-weight: 600; }\n"
        "    h2 { color: #004085; font-size: 1.5rem; margin-top: 30px; border-left: 4px solid #0056b3; padding-left: 10px; }\n"
        "    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }\n"
        "    .card { background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 92, 179, 0.08); border: 1px solid #e2e8f0; }\n"
        "    .label { color: #004085; font-size: 14px; margin-bottom: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }\n"
        "    button { background: #0056b3; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin: 5px; font-weight: 500; transition: background 0.2s; }\n"
        "    button:hover { background: #004494; }\n"
        "    .btn-stop { background: #dc3545; }\n"
        "    .btn-stop:hover { background: #b02a37; }\n"
        "    .btn-secondary { background: #e2e8f0; color: #333; }\n"
        "    .btn-secondary:hover { background: #cbd5e1; }\n"
        "    input, select { padding: 10px; margin: 5px; border: 1px solid #cbd5e1; border-radius: 6px; width: calc(100% - 20px); box-sizing: border-box; font-family: inherit; }\n"
        "    input:focus, select:focus { outline: none; border-color: #0056b3; box-shadow: 0 0 0 3px rgba(0, 86, 179, 0.1); }\n"
        "    .output { background: #f8fafc; padding: 15px; border-radius: 6px; font-family: Consolas, monospace; white-space: pre-wrap; max-height: 400px; overflow-y: auto; margin-top: 15px; border: 1px solid #e2e8f0; color: #1e293b; line-height: 1.5; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <div class=\"container\">\n"
        "    <h1>🖥️ Dynamic Resource Allocator</h1>\n"
        "\n"
        "    <div class=\"grid\">\n"
        "      <div class=\"card\">\n"
        "        <div class=\"label\">System Control</div>\n"
        "        <button onclick=\"startSystem()\">▶️ Start System</button>\n"
        "        <button class=\"btn-stop\" onclick=\"stopSystem()\">⏹️ Stop System</button>\n"
        "        <div id=\"status\" class=\"output\">Status will appear here...</div>\n"
        "      </div>\n"
        "      <div class=\"card\">\n"
        "        <div class=\"label\">Strategy & Process Runner</div>\n"
        "        <select id=\"strategy-select\">\n"
        "          <option value=\"0\">Equal</option>\n"
        "          <option value=\"1\">Priority</option>\n"
        "          <option value=\"2\" selected>Performance</option>\n"
        "          <option value=\"3\">Demand</option>\n"
        "        </select>\n"
        "        <button onclick=\"setStrategy()\">Apply Strategy</button>\n"
        "        <div id=\"strategy-out\" style=\"margin-top:5px; margin-bottom: 15px; color: #0056b3; font-weight: 500;\"></div>\n"
        "        <hr style=\"border:0; border-top:1px solid #e2e8f0; margin:15px 0;\">\n"
        "        <div class=\"label\">Start New Process</div>\n"
        "        <input type=\"text\" id=\"new-cmd\" placeholder=\"e.g. sleep 60\">\n"
        "        <button onclick=\"startProcess()\">Start Process</button>\n"
        "        <div id=\"cmd-out\" style=\"margin-top:5px; color: #0056b3; font-weight: 500;\"></div>\n"
        "      </div>\n"
        "    </div>\n"
        "\n"
        "    <div>\n"
        "      <h2>Monitor & Reports</h2>\n"
        "      <div class=\"grid\">\n"
        "        <div class=\"card\">\n"
        "          <div class=\"label\">Live Monitor</div>\n"
        "          <button class=\"btn-secondary\" onclick=\"getStatus()\">🔄 Refresh</button>\n"
        "          <div id=\"monitor\" class=\"output\">Monitoring data...</div>\n"
        "        </div>\n"
        "        <div class=\"card\" style=\"grid-column: span 2;\">\n"
        "          <div class=\"label\">Real-time System Impact Graph</div>\n"
        "          <canvas id=\"impactChart\" height=\"80\"></canvas>\n"
        "        </div>\n"
        "        <div class=\"card\">\n"
        "          <div class=\"label\">Comprehensive Report</div>\n"
        "          <button class=\"btn-secondary\" onclick=\"getReport()\">📊 Generate Full Report</button>\n"
        "          <div id=\"report\" class=\"output\">System analysis...</div>\n"
        "        </div>\n"
        "      </div>\n"
        "    </div>\n"
        "\n"
        "    <div>\n"
        "      <h2>Programs</h2>\n"
        "      <div class=\"card\">\n"
        "        <button class=\"btn-secondary\" onclick=\"getAvailablePids()\">🔍 Show Available PIDs</button>\n"
        "        <div id=\"available-pids\" class=\"output\"></div>\n"
        "      </div>\n"
        "      <div class=\"grid\" style=\"margin-top: 20px;\">\n"
        "        <div class=\"card\">\n"
        "          <div class=\"label\">Register Process</div>\n"
        "          <input type=\"number\" id=\"pid\" placeholder=\"PID\" min=\"1\">\n"
        "          <input type=\"text\" id=\"name\" placeholder=\"Process Name\">\n"
        "          <select id=\"priority\">\n"
        "            <option value=\"3\">NORMAL</option>\n"
        "            <option value=\"5\">CRITICAL</option>\n"
        "            <option value=\"4\">HIGH</option>\n"
        "            <option value=\"2\">LOW</option>\n"
        "            <option value=\"1\">BACKGROUND</option>\n"
        "          </select>\n"
        "          <button onclick=\"registerProcess()\">Register</button>\n"
        "          <div id=\"register-out\" style=\"margin-top:5px; color: #0056b3; font-weight: 500;\"></div>\n"
        "        </div>\n"
        "        <div class=\"card\">\n"
        "          <div class=\"label\">Management</div>\n"
        "          <input type=\"number\" id=\"update-pid\" placeholder=\"PID\" min=\"1\">\n"
        "          <select id=\"new-priority\">\n"
        "            <option value=\"3\">NORMAL</option>\n"
        "            <option value=\"5\">CRITICAL</option>\n"
        "            <option value=\"4\">HIGH</option>\n"
        "            <option value=\"2\">LOW</option>\n"
        "            <option value=\"1\">BACKGROUND</option>\n"
        "          </select>\n"
        "          <button onclick=\"updatePriority()\">Update Priority</button>\n"
        "          <button class=\"btn-stop\" onclick=\"unregisterProcess()\">Unregister Process</button>\n"
        "          <div id=\"manage-out\" style=\"margin-top:5px; color: #0056b3; font-weight: 500;\"></div>\n"
        "        </div>\n"
        "      </div>\n"
        "      <div class=\"card\" style=\"margin-top: 20px;\">\n"
        "        <div class=\"label\">Tracked Programs</div>\n"
        "        <button class=\"btn-secondary\" onclick=\"getTracked()\">🔄 Auto-Refresh Tracked</button>\n"
        "        <div id=\"tracked\" class=\"output\"></div>\n"
        "      </div>\n"
        "    </div>\n"
        "\n"
        "    <div>\n"
        "      <h2>Workload Testing &amp; Live Impact</h2>\n"
        "      <div class=\"grid\">\n"
        "        <div class=\"card\">\n"
        "          <div class=\"label\">CPU Stress</div>\n"
        "          <label style=\"font-size:12px;\">Intensity: <span id=\"cpu-val\">50</span>%</label><br>\n"
        "          <input type=\"range\" id=\"cpu-intensity\" min=\"0\" max=\"100\" value=\"50\" oninput=\"document.getElementById('cpu-val').innerText=this.value\">\n"
        "          <button class=\"btn-secondary\" onclick=\"startCPUWorkload()\">Start CPU Load</button>\n"
        "          <div id=\"cpu-out\" style=\"margin-top:5px; color: #0056b3; font-weight: 500;\"></div>\n"
        "        </div>\n"
        "        <div class=\"card\">\n"
        "          <div class=\"label\">Memory Stress</div>\n"
        "          <label style=\"font-size:12px;\">Allocate: <span id=\"mem-val\">100</span> MB</label><br>\n"
        "          <input type=\"range\" id=\"mem-size\" min=\"1\" max=\"500\" value=\"100\" oninput=\"document.getElementById('mem-val').innerText=this.value\">\n"
        "          <button class=\"btn-secondary\" onclick=\"startMemWorkload()\">Start Memory Load</button>\n"
        "          <div id=\"mem-out\" style=\"margin-top:5px; color: #0056b3; font-weight: 500;\"></div>\n"
        "        </div>\n"
        "        <div class=\"card\">\n"
        "          <div class=\"label\">I/O Stress</div>\n"
        "          <label style=\"font-size:12px;\">Files: <span id=\"io-val\">10</span></label><br>\n"
        "          <input type=\"range\" id=\"io-files\" min=\"1\" max=\"50\" value=\"10\" oninput=\"document.getElementById('io-val').innerText=this.value\">\n"
        "          <button class=\"btn-secondary\" onclick=\"startIOWorkload()\">Start I/O Load</button>\n"
        "          <div id=\"io-out\" style=\"margin-top:5px; color: #0056b3; font-weight: 500;\"></div>\n"
        "        </div>\n"
        "        <div class=\"card\">\n"
        "          <div class=\"label\">Control</div>\n"
        "          <button class=\"btn-stop\" onclick=\"stopAllWorkloads()\" style=\"width:calc(100% - 10px)\">Stop All Workloads</button>\n"
        "        </div>\n"
        "      </div>\n"
        "      <div class=\"card\" style=\"margin-top:20px;\">\n"
        "        <div class=\"label\">Live Workload Impact Dashboard</div>\n"
        "        <div style=\"display:grid; grid-template-columns:1fr 1fr 1fr; gap:20px; margin-bottom:20px;\">\n"
        "          <div>\n"
        "            <div style=\"font-size:11px; color:#004085; font-weight:700; margin-bottom:6px; letter-spacing:1px;\">CPU IMPACT</div>\n"
        "            <div style=\"background:#e2e8f0; border-radius:8px; height:24px; overflow:hidden;\">\n"
        "              <div id=\"wl-cpu-bar\" style=\"height:100%; width:0%; background:linear-gradient(90deg,#0056b3,#38bdf8); transition:width 0.6s ease; border-radius:8px;\"></div>\n"
        "            </div>\n"
        "            <div id=\"wl-cpu-pct\" style=\"font-size:1.4rem; font-weight:700; color:#0056b3; margin-top:4px;\">0%</div>\n"
        "          </div>\n"
        "          <div>\n"
        "            <div style=\"font-size:11px; color:#004085; font-weight:700; margin-bottom:6px; letter-spacing:1px;\">MEMORY IMPACT</div>\n"
        "            <div style=\"background:#e2e8f0; border-radius:8px; height:24px; overflow:hidden;\">\n"
        "              <div id=\"wl-mem-bar\" style=\"height:100%; width:0%; background:linear-gradient(90deg,#dc3545,#f97316); transition:width 0.6s ease; border-radius:8px;\"></div>\n"
        "            </div>\n"
        "            <div id=\"wl-mem-pct\" style=\"font-size:1.4rem; font-weight:700; color:#dc3545; margin-top:4px;\">0%</div>\n"
        "          </div>\n"
        "          <div>\n"
        "            <div style=\"font-size:11px; color:#004085; font-weight:700; margin-bottom:6px; letter-spacing:1px;\">ACTIVE WORKLOADS</div>\n"
        "            <div id=\"wl-count\" style=\"font-size:2.5rem; font-weight:800; color:#0056b3; line-height:1;\">0</div>\n"
        "            <div id=\"wl-status\" style=\"font-size:12px; color:#888; margin-top:4px;\">Idle - no workloads running</div>\n"
        "          </div>\n"
        "        </div>\n"
        "        <div style=\"font-size:11px; color:#004085; font-weight:700; margin-bottom:6px; letter-spacing:1px;\">WORKLOAD EVENT LOG</div>\n"
        "        <div id=\"wl-log\" class=\"output\" style=\"max-height:180px; font-size:12px;\">No workloads started yet.</div>\n"
        "      </div>\n"
        "    </div>\n"
        "  </div>\n"
        "\n"
        "  <script>\n"
        "    let impactChart;\n"
        "    const maxDataPoints = 20;\n"
        "    function initChart() {\n"
        "      const ctx = document.getElementById(\'impactChart\').getContext(\'2d\');\n"
        "      impactChart = new Chart(ctx, {\n"
        "        type: \'line\',\n"
        "        data: {\n"
        "          labels: Array(maxDataPoints).fill(\'\'),\n"
        "          datasets: [\n"
        "            { label: \'CPU Usage (%)\', borderColor: \'#0056b3\', backgroundColor: \'rgba(0, 86, 179, 0.1)\', data: Array(maxDataPoints).fill(0), fill: true, tension: 0.4 },\n"
        "            { label: \'Memory Usage (%)\', borderColor: \'#dc3545\', backgroundColor: \'rgba(220, 53, 69, 0.1)\', data: Array(maxDataPoints).fill(0), fill: true, tension: 0.4 }\n"
        "          ]\n"
        "        },\n"
        "        options: {\n"
        "          responsive: true,\n"
        "          animation: { duration: 0 },\n"
        "          scales: { y: { min: 0, max: 100 } }\n"
        "        }\n"
        "      });\n"
        "    }\n"
        "    \n"
        "    function updateChart(cpu, mem) {\n"
        "      if(!impactChart) return;\n"
        "      impactChart.data.datasets[0].data.shift();\n"
        "      impactChart.data.datasets[0].data.push(cpu);\n"
        "      impactChart.data.datasets[1].data.shift();\n"
        "      impactChart.data.datasets[1].data.push(mem);\n"
        "      impactChart.update();\n"
        "    }\n"
        "    async function apiCall(endpoint, method = 'GET', data = null, expectText = false) {\n"
        "      const options = { method };\n"
        "      if (data) {\n"
        "        options.headers = { 'Content-Type': 'application/json' };\n"
        "        options.body = JSON.stringify(data);\n"
        "      }\n"
        "      const response = await fetch('/api' + endpoint, options);\n"
        "      if(expectText) return await response.text();\n"
        "      return await response.json();\n"
        "    }\n"
        "\n"
        "    async function startSystem() {\n"
        "      const result = await apiCall('/start', 'POST');\n"
        "      document.getElementById('status').innerText = result.message;\n"
        "    }\n"
        "    async function stopSystem() {\n"
        "      const result = await apiCall('/stop', 'POST');\n"
        "      document.getElementById('status').innerText = result.message;\n"
        "    }\n"
        "    async function setStrategy() {\n"
        "      const strategy = parseInt(document.getElementById('strategy-select').value);\n"
        "      const result = await apiCall('/set-strategy', 'POST', {strategy});\n"
        "      document.getElementById('strategy-out').innerText = result.message;\n"
        "    }\n"
        "    async function startProcess() {\n"
        "      const command = document.getElementById('new-cmd').value;\n"
        "      const result = await apiCall('/start-process', 'POST', {command});\n"
        "      document.getElementById('cmd-out').innerText = result.message;\n"
        "      setTimeout(() => document.getElementById('cmd-out').innerText = '', 3000);\n"
        "    }\n"
        "    async function getStatus() {\n"
        "      const result = await apiCall('/status');\n"
        "      let text = 'System Status\\n============\\n';\n"
        "      text += `Running: ${result.running ? 'Yes ✓' : 'No ✗'}\\n`;\n"
        "      text += `Uptime: ${result.uptime_seconds}s\\n`;\n"
        "      text += `CPU: ${result.cpu_percent.toFixed(1)}%\\n`;\n"
        "      text += `Memory: ${result.memory_percent.toFixed(1)}%\\n`;\n"
        "      text += `Tracked Programs: ${result.tracked_programs}\\n`;\n"
        "      text += `Active Workloads: ${result.active_workloads}\\n`;\n"
        "      document.getElementById('monitor').innerText = text;\n"
        "      updateChart(result.cpu_percent, result.memory_percent);\n"
        "      updateWorkloadDashboard(result.cpu_percent, result.memory_percent, result.active_workloads);\n"
        "    }\n"
        "    async function getReport() {\n"
        "      const text = await apiCall('/report', 'GET', null, true);\n"
        "      document.getElementById('report').innerText = text;\n"
        "    }\n"
        "    async function getAvailablePids() {\n"
        "      const text = await apiCall('/available-pids', 'GET', null, true);\n"
        "      document.getElementById('available-pids').innerText = text;\n"
        "    }\n"
        "    async function registerProcess() {\n"
        "      const pid = parseInt(document.getElementById('pid').value);\n"
        "      const name = document.getElementById('name').value;\n"
        "      const priority = parseInt(document.getElementById('priority').value);\n"
        "      const result = await apiCall('/register-process', 'POST', {pid, name, priority});\n"
        "      document.getElementById('register-out').innerText = result.message;\n"
        "      setTimeout(() => document.getElementById('register-out').innerText = '', 3000);\n"
        "    }\n"
        "    async function updatePriority() {\n"
        "      const pid = parseInt(document.getElementById('update-pid').value);\n"
        "      const priority = parseInt(document.getElementById('new-priority').value);\n"
        "      const result = await apiCall('/set-priority', 'POST', {pid, priority});\n"
        "      document.getElementById('manage-out').innerText = result.message;\n"
        "      setTimeout(() => document.getElementById('manage-out').innerText = '', 3000);\n"
        "    }\n"
        "    async function unregisterProcess() {\n"
        "      const pid = parseInt(document.getElementById('update-pid').value);\n"
        "      const result = await apiCall('/unregister-process', 'POST', {pid});\n"
        "      document.getElementById('manage-out').innerText = result.message;\n"
        "      setTimeout(() => document.getElementById('manage-out').innerText = '', 3000);\n"
        "    }\n"
        "    async function getTracked() {\n"
        "      const result = await apiCall('/tracked');\n"
        "      let text = 'Tracked Programs\\n================\\n';\n"
        "      if(result.tracked.length === 0) text += 'None';\n"
        "      result.tracked.forEach(proc => {\n"
        "        text += `PID: ${proc.pid} - ${proc.name} (${proc.priority}) | CPU: ${proc.cpu}% | Mem: ${proc.memory}%\\n`;\n"
        "      });\n"
        "      document.getElementById('tracked').innerText = text;\n"
        "    }\n"
        "    async function startCPUWorkload() {\n"
        "      const intensity = document.getElementById('cpu-intensity').value;\n"
        "      const result = await apiCall('/workload-cpu', 'POST', {intensity: parseInt(intensity)});\n"
        "      document.getElementById('cpu-out').innerText = result.message;\n"
        "      wlLog('CPU workload started at intensity '+intensity+'%');\n"
        "      setTimeout(() => document.getElementById('cpu-out').innerText = '', 5000);\n"
        "    }\n"
        "    async function startMemWorkload() {\n"
        "      const size = document.getElementById('mem-size').value;\n"
        "      const result = await apiCall('/workload-memory', 'POST', {size: parseInt(size)});\n"
        "      document.getElementById('mem-out').innerText = result.message;\n"
        "      wlLog('Memory workload started at '+size+' MB');\n"
        "      setTimeout(() => document.getElementById('mem-out').innerText = '', 5000);\n"
        "    }\n"
        "    async function startIOWorkload() {\n"
        "      const files = document.getElementById('io-files').value;\n"
        "      const result = await apiCall('/workload-io', 'POST', {files: parseInt(files)});\n"
        "      document.getElementById('io-out').innerText = result.message;\n"
        "      wlLog('I/O workload started with '+files+' files');\n"
        "      setTimeout(() => document.getElementById('io-out').innerText = '', 5000);\n"
        "    }\n"
        "    async function stopAllWorkloads() {\n"
        "      const result = await apiCall('/workload-stop', 'POST');\n"
        "      wlLog('All workloads stopped: '+result.message);\n"
        "      alert(result.message);\n"
        "    }\n"
        "    let wlBaselineCpu = null, wlBaselineMem = null;\n"
        "    function wlLog(msg) {\n"
        "      const d = new Date(); const t = d.getHours()+':'+String(d.getMinutes()).padStart(2,'0')+':'+String(d.getSeconds()).padStart(2,'0');\n"
        "      const el = document.getElementById('wl-log');\n"
        "      el.innerText = '['+t+'] '+msg+'\\n' + el.innerText;\n"
        "    }\n"
        "    function updateWorkloadDashboard(cpu, mem, workloads) {\n"
        "      document.getElementById('wl-cpu-bar').style.width = Math.min(cpu,100)+'%';\n"
        "      document.getElementById('wl-cpu-pct').innerText = cpu.toFixed(1)+'%';\n"
        "      document.getElementById('wl-mem-bar').style.width = Math.min(mem,100)+'%';\n"
        "      document.getElementById('wl-mem-pct').innerText = mem.toFixed(1)+'%';\n"
        "      document.getElementById('wl-count').innerText = workloads;\n"
        "      const status = workloads > 0 ? '\xe2\x9a\xa1 '+workloads+' workload(s) actively stressing system' : 'Idle - no workloads running';\n"
        "      document.getElementById('wl-status').innerText = status;\n"
        "    }\n"
        "    setInterval(getStatus, 2000);\n"
        "    setInterval(getTracked, 2000);\n"
        "    initChart();\n"
        "    getStatus();\n"
        "    getTracked();\n"
        "  </script>\n"
        "</body>\n"
        "</html>\n";
    return (char*)html;
}


void handle_http_request(int client_sock, const char *buffer, int len) {
    HttpRequest req;
    parse_http_request(buffer, len, &req);
    
    // Route handling
    if (strcmp(req.path, "/") == 0) {
        send_http_response(client_sock, 200, "text/html; charset=UTF-8", get_html_page());
    }
    
    else if (strcmp(req.path, "/api/available-pids") == 0) {
        send_http_response(client_sock, 200, "text/plain; charset=UTF-8", get_available_pids_text());
    }
    else if (strcmp(req.path, "/api/report") == 0) {
        send_http_response(client_sock, 200, "text/plain; charset=UTF-8", get_report_text());
    }
    else if (strcmp(req.path, "/api/set-strategy") == 0 && strcmp(req.method, "POST") == 0) {
        int strategy_val = json_get_int(req.body, "strategy");
        if(strategy_val >= 0 && strategy_val <= 3) {
            state.strategy = (AllocationStrategy)strategy_val;
            send_http_response(client_sock, 200, "application/json", "{\"message\":\"✅ Strategy updated\"}");
        } else {
            send_http_response(client_sock, 200, "application/json", "{\"message\":\"❌ Invalid strategy\"}");
        }
    }
    else if (strcmp(req.path, "/api/status") == 0) {
        send_http_response(client_sock, 200, "application/json", get_status_json());
    }
    else if (strcmp(req.path, "/api/tracked") == 0) {
        send_http_response(client_sock, 200, "application/json", get_tracked_json());
    }
    else if (strcmp(req.path, "/api/start-process") == 0 && strcmp(req.method, "POST") == 0) {
        char command[512] = {0};
        json_get_string(req.body, "command", command, sizeof(command));
        if (command[0]) {
            /* Tokenise the command string into argv — no shell involved */
            char *argv[64];
            int argc = 0;
            char cmd_copy[512];
            strncpy(cmd_copy, command, sizeof(cmd_copy) - 1);
            char *tok = strtok(cmd_copy, " ");
            while (tok && argc < 63) { argv[argc++] = tok; tok = strtok(NULL, " "); }
            argv[argc] = NULL;

            pid_t pid = fork();
            if (pid == 0) {
                /* Child: detach from parent's session, then exec directly */
                setsid();
                execvp(argv[0], argv);
                _exit(127); /* exec failed */
            } else if (pid > 0) {
                char msg[256];
                snprintf(msg, sizeof(msg), "{\"message\":\"✅ Process started (PID: %d)\"}", pid);
                send_http_response(client_sock, 200, "application/json", msg);
            } else {
                send_http_response(client_sock, 500, "application/json", "{\"message\":\"❌ fork() failed\"}");
            }
        } else {
            send_http_response(client_sock, 200, "application/json", "{\"message\":\"❌ Invalid command\"}");
        }
    }
    else if (strcmp(req.path, "/api/start") == 0 && strcmp(req.method, "POST") == 0) {
        state.running = 1;
        state.start_time = time(NULL);
        send_http_response(client_sock, 200, "application/json", "{\"message\":\"✅ System started\"}");
    }
    else if (strcmp(req.path, "/api/stop") == 0 && strcmp(req.method, "POST") == 0) {
        state.running = 0;
        send_http_response(client_sock, 200, "application/json", "{\"message\":\"✅ System stopped\"}");
    }
    else if (strcmp(req.path, "/api/register-process") == 0 && strcmp(req.method, "POST") == 0) {
        int pid = json_get_int(req.body, "pid");
        char name[256] = {0};
        json_get_string(req.body, "name", name, sizeof(name));
        int priority = json_get_int(req.body, "priority");
        
        if (pid > 0 && name[0]) {
            if (register_process(pid, name, (ProcessPriority)priority)) {
                send_http_response(client_sock, 200, "application/json", 
                    "{\"message\":\"✅ Process registered\"}");
            } else {
                send_http_response(client_sock, 200, "application/json", 
                    "{\"message\":\"❌ Failed to register process\"}");
            }
        } else {
            send_http_response(client_sock, 200, "application/json", 
                "{\"message\":\"❌ Invalid PID or name\"}");
        }
    }
    else if (strcmp(req.path, "/api/unregister-process") == 0 && strcmp(req.method, "POST") == 0) {
        int pid = json_get_int(req.body, "pid");
        if (unregister_process(pid)) {
            send_http_response(client_sock, 200, "application/json", 
                "{\"message\":\"✅ Process unregistered\"}");
        } else {
            send_http_response(client_sock, 200, "application/json", 
                "{\"message\":\"❌ Process not found\"}");
        }
    }
    else if (strcmp(req.path, "/api/set-priority") == 0 && strcmp(req.method, "POST") == 0) {
        int pid = json_get_int(req.body, "pid");
        int priority = json_get_int(req.body, "priority");
        if (set_priority(pid, (ProcessPriority)priority)) {
            send_http_response(client_sock, 200, "application/json", 
                "{\"message\":\"✅ Priority updated\"}");
        } else {
            send_http_response(client_sock, 200, "application/json", 
                "{\"message\":\"❌ Process not found\"}");
        }
    }
    else if (strcmp(req.path, "/api/workload-cpu") == 0 && strcmp(req.method, "POST") == 0) {
        int intensity = json_get_int(req.body, "intensity");
        if (intensity < 0) intensity = 50;
        if (intensity > 100) intensity = 100;
        
        pthread_t tid;
        int *arg = malloc(sizeof(int));
        *arg = intensity;
        
        if (pthread_create(&tid, NULL, cpu_workload_thread, arg) == 0) {
            pthread_detach(tid);
            state.active_workloads++;
            send_http_response(client_sock, 200, "application/json", 
                "{\"message\":\"✅ CPU workload started (30s duration)\"}");
        } else {
            free(arg);
            send_http_response(client_sock, 200, "application/json", 
                "{\"message\":\"❌ Failed to start workload\"}");
        }
    }
    else if (strcmp(req.path, "/api/workload-memory") == 0 && strcmp(req.method, "POST") == 0) {
        int size = json_get_int(req.body, "size");
        if (size < 1) size = 100;
        if (size > 500) size = 500;
        
        pthread_t tid;
        int *arg = malloc(sizeof(int));
        *arg = size;
        
        if (pthread_create(&tid, NULL, memory_workload_thread, arg) == 0) {
            pthread_detach(tid);
            state.active_workloads++;
            send_http_response(client_sock, 200, "application/json", 
                "{\"message\":\"✅ Memory workload started (30s duration)\"}");
        } else {
            free(arg);
            send_http_response(client_sock, 200, "application/json", 
                "{\"message\":\"❌ Failed to start workload\"}");
        }
    }
    else if (strcmp(req.path, "/api/workload-io") == 0 && strcmp(req.method, "POST") == 0) {
        int files = json_get_int(req.body, "files");
        if (files < 1) files = 10;
        if (files > 100) files = 100;
        
        pthread_t tid;
        int *arg = malloc(sizeof(int));
        *arg = files;
        
        if (pthread_create(&tid, NULL, io_workload_thread, arg) == 0) {
            pthread_detach(tid);
            state.active_workloads++;
            send_http_response(client_sock, 200, "application/json", 
                "{\"message\":\"✅ I/O workload started (30s duration)\"}");
        } else {
            free(arg);
            send_http_response(client_sock, 200, "application/json", 
                "{\"message\":\"❌ Failed to start workload\"}");
        }
    }
    else if (strcmp(req.path, "/api/workload-stop") == 0 && strcmp(req.method, "POST") == 0) {
        state.shutdown_flag = 1;
        sleep(2);
        state.shutdown_flag = 0;
        send_http_response(client_sock, 200, "application/json", 
            "{\"message\":\"✅ All workloads stopped\"}");
    }
    else {
        send_http_response(client_sock, 404, "application/json", 
            "{\"message\":\"404 Not Found\"}");
    }
}

void* server_thread_func(void *arg) {
    int server_sock = socket(AF_INET, SOCK_STREAM, 0);
    if (server_sock < 0) {
        perror("socket");
        return NULL;
    }
    
    int opt = 1;
    setsockopt(server_sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(PORT);
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    
    if (bind(server_sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_sock);
        return NULL;
    }
    
    listen(server_sock, 20);
    printf("🌐 Web Server listening on http://localhost:%d\n", PORT);
    printf("✅ All endpoints active and ready\n\n");
    
    while (!state.shutdown_flag) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        int client_sock = accept(server_sock, (struct sockaddr *)&client_addr, &client_len);
        
        if (client_sock < 0) continue;
        
        char buffer[BUFFER_SIZE];
        int bytes = recv(client_sock, buffer, sizeof(buffer) - 1, 0);
        
        if (bytes > 0) {
            buffer[bytes] = '\0';
            handle_http_request(client_sock, buffer, bytes);
        }
        
        close(client_sock);
    }
    
    close(server_sock);
    return NULL;
}

void* monitor_thread_func(void *arg) {
    while (!state.shutdown_flag && state.running) {
        collect_metrics();
        sleep(1);
    }
    return NULL;
}

void* optimizer_thread_func(void *arg) {
    while (!state.shutdown_flag && state.running) {
        apply_adaptive_control();
        sleep(5);
    }
    return NULL;
}

/* ============================================================================
 * MAIN APPLICATION
 * ============================================================================ */

int main() {
    printf("\n");
    printf("================================================================================\n");
    printf("🖥️  DYNAMIC RESOURCE ALLOCATOR - FULL-FEATURED C IMPLEMENTATION\n");
    printf("================================================================================\n");
    printf("\n✅ System Components:\n");
    printf("   • System Monitor (Real-time CPU/Memory metrics)\n");
    printf("   • Process Manager (Full tracking table with per-process stats)\n");
    printf("   • Performance Optimizer (Adaptive resource control)\n");
    printf("   • Workload Simulator (CPU/Memory/I/O stress testing)\n");
    printf("\n✅ Web Interface:\n");
    printf("   • Embedded HTTP/1.1 Server\n");
    printf("   • Interactive HTML5/CSS3/JavaScript UI\n");
    printf("   • RESTful JSON API with full request/response handling\n");
    printf("\n✅ API Endpoints:\n");
    printf("   • GET  /api/status - System status and metrics\n");
    printf("   • GET  /api/tracked - List all tracked processes\n");
    printf("   • POST /api/start - Start system monitoring\n");
    printf("   • POST /api/stop - Stop system monitoring\n");
    printf("   • POST /api/register-process - Register process for tracking\n");
    printf("   • POST /api/unregister-process - Unregister process\n");
    printf("   • POST /api/set-priority - Set process priority\n");
    printf("   • POST /api/workload-cpu - Start CPU stress test\n");
    printf("   • POST /api/workload-memory - Start memory stress test\n");
    printf("   • POST /api/workload-io - Start I/O stress test\n");
    printf("   • POST /api/workload-stop - Stop all workloads\n");
    printf("\n🌐 Web Interface: http://localhost:%d\n", PORT);
    printf("================================================================================\n\n");
    
    // Initialize state
    pthread_mutex_init(&state.lock, NULL);
    state.strategy = STRATEGY_PERFORMANCE;
    state.running = 0;
    state.start_time = time(NULL);
    state.shutdown_flag = 0;
    state.tracked_count = 0;
    state.active_workloads = 0;
    state.history_count = 0;
    
    // Start server thread (always running)
    pthread_create(&state.server_thread, NULL, server_thread_func, NULL);
    sleep(1);
    
    // Monitor and optimizer threads will be controlled by client through web UI
    // Start system
    state.running = 1;
    pthread_create(&state.monitor_thread, NULL, monitor_thread_func, NULL);
    pthread_create(&state.optimizer_thread, NULL, optimizer_thread_func, NULL);
    
    printf("✅ System started and ready to accept requests\n");
    printf("📊 Navigate to http://localhost:%d in your web browser\n\n", PORT);
    
    // Keep alive
    while (!state.shutdown_flag) {
        sleep(1);
    }
    
    state.shutdown_flag = 1;
    sleep(2);
    pthread_mutex_destroy(&state.lock);
    
    printf("\n✅ System shutdown complete\n");
    return 0;
}
