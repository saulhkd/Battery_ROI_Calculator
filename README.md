# Batt_saving
docker build -t simulador-baterias .
docker run --rm -v $(pwd)/resultados:/app/resultados simulador-baterias
