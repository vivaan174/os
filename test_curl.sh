curl -s -X POST -H "Content-Type: application/json" -d '{"command":"sleep 30"}' http://localhost:7860/api/start-process
echo ""
curl -s -X POST -H "Content-Type: application/json" -d '{"intensity":80}' http://localhost:7860/api/workload-cpu
echo ""
curl -s http://localhost:7860/api/status
