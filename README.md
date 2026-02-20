🔋 Simulador de Rentabilidad de Baterías Industriales (Battery ROI Calculator)
Esta herramienta es un simulador avanzado desarrollado en Python diseñado para calcular el Retorno de Inversión (ROI) de instalaciones de almacenamiento de energía (baterías) en entornos industriales o comerciales.

El proyecto nació como una herramienta comercial para demostrar la viabilidad de instalar baterías de 100kWh combinando dos estrategias fundamentales:

Autoconsumo de excedentes solares: Guardar la energía que sobra por el día para no venderla barata a la red.

Arbitraje de Red: Cargar la batería por la noche (cuando el precio en tarifas indexadas es muy bajo) y descargarla en las horas pico (cuando la luz es más cara).

🚀 Características Principales
Simulación Matemática Avanzada: Genera perfiles sintéticos de consumo y generación solar cuarto-horarios u horarios a partir de datos mensuales de facturas.

Interfaz Web Interactiva (Streamlit): Permite modificar en tiempo real parámetros como el tamaño de la batería, el coste de instalación y los precios de compra/venta de energía para ver cómo afecta al ROI en directo.

Comparativa de Tarifas: Demuestra visualmente por qué una batería es mucho más rentable bajo una Tarifa Indexada frente a una Tarifa Fija.

Soporte para Docker: Contenerización completa para ejecutar la aplicación web o los scripts de cálculo en cualquier entorno sin problemas de dependencias.

📂 Estructura del Repositorio
appstream.py: La aplicación web interactiva desarrollada con Streamlit. Es la herramienta ideal para presentar los resultados al cliente final.

arbitraje-y-solar.py: Script de consola que ejecuta la simulación avanzada hora a hora, combinando el uso de excedentes solares y la compra de energía de la red en horas valle.

main.py: Script de simulación básica que utiliza únicamente los datos mensuales y promedios diarios extraídos de las facturas en PDF.

requirements.txt: Lista de dependencias y librerías de Python necesarias para el proyecto.

Dockerfile: Archivo de configuración para crear la imagen de Docker del proyecto.

🛠️ Instalación y Uso (Entorno Local)
Si deseas ejecutar el código directamente en tu ordenador (recomendado para la demostración con el cliente):

Clona el repositorio y navega a la carpeta del proyecto.

Instala las dependencias requeridas:

Bash
pip install -r requirements.txt
Ejecuta la interfaz web (Streamlit):

Bash
streamlit run appstream.py
Esto abrirá automáticamente una pestaña en tu navegador web (usualmente en http://localhost:8501).

Ejecutar simulaciones por consola (generan gráficas .png en la carpeta /resultados):

Bash
python arbitraje-y-solar.py
# o
python main.py
🐳 Instalación y Uso (Docker)
Si prefieres aislar el entorno utilizando Docker:

Construye la imagen de Docker:

Bash
docker build -t simulador-baterias .
Ejecutar un script de consola (montando un volumen para extraer las gráficas generadas):
En PowerShell (Windows):

PowerShell
docker run --rm -v "${PWD}/resultados:/app/resultados" simulador-baterias
En Bash (Mac/Linux):

Bash
docker run --rm -v $(pwd)/resultados:/app/resultados simulador-baterias
(Nota: Si deseas que Docker ejecute la aplicación web de Streamlit, asegúrate de modificar el Dockerfile para exponer el puerto 8501 y cambiar el ENTRYPOINT a ["streamlit", "run", "appstream.py"], y luego ejecuta docker run -p 8501:8501 simulador-baterias).

💼 Caso de Uso (Argumentario Comercial)
Este software permite desmentir simulaciones infladas de la competencia. Al ajustar la tabla de precios dentro de la aplicación (por ejemplo, bajando el precio Valle a 0.05 € para simular un contrato indexado), el simulador demuestra cómo una batería más económica y dimensionada correctamente (100kWh/50kW) puede ofrecer retornos de inversión de 6 a 7 años, superando ampliamente las propuestas de baterías sobredimensionadas que dependen de condiciones tarifarias ocultas para mostrar rentabilidad.
-------------------------------------------------------------------------------------------
🔋 Industrial Battery ROI Simulator (Battery ROI Calculator)
This tool is an advanced simulator developed in Python designed to calculate the Return on Investment (ROI) of energy storage installations (batteries) in industrial or commercial environments.

The project was born as a commercial tool to demonstrate the viability of installing 100kWh batteries combining two fundamental strategies:

Solar surplus self-consumption: Storing excess energy generated during the day to avoid selling it cheaply to the grid.

Grid Arbitrage: Charging the battery at night (when the price in indexed tariffs is very low) and discharging it during peak hours (when electricity is more expensive).

🚀 Main Features
Advanced Mathematical Simulation: Generates synthetic quarter-hourly or hourly consumption and solar generation profiles from monthly invoice data.

Interactive Web Interface (Streamlit): Allows real-time modification of parameters such as battery size, installation cost, and energy purchase/sale prices to see how they affect the ROI live.

Tariff Comparison: Visually demonstrates why a battery is much more profitable under an Indexed Tariff compared to a Fixed Tariff.

Docker Support: Complete containerization to run the web application or calculation scripts in any environment without dependency issues.

📂 Repository Structure
appstream.py: The interactive web application developed with Streamlit. It is the ideal tool for presenting results to the end client.

arbitraje-y-solar.py: Console script that runs the advanced hour-by-hour simulation, combining the use of solar surplus and grid energy purchase during off-peak hours.

main.py: Basic simulation script that uses only the monthly data and daily averages extracted from the PDF invoices.

requirements.txt: List of Python dependencies and libraries required for the project.

Dockerfile: Configuration file to build the Docker image of the project.

🛠️ Installation and Usage (Local Environment)
If you wish to run the code directly on your computer (recommended for client demonstrations):

Clone the repository and navigate to the project folder.

Install the required dependencies:

Bash
pip install -r requirements.txt
Run the web interface (Streamlit):

Bash
streamlit run appstream.py
This will automatically open a tab in your web browser (usually at http://localhost:8501).

Run console simulations (generates .png graphs in the /resultados folder):

Bash
python arbitraje-y-solar.py
# or
python main.py
🐳 Installation and Usage (Docker)
If you prefer to isolate the environment using Docker:

Build the Docker image:

Bash
docker build -t simulador-baterias .
Run a console script (mounting a volume to extract the generated graphs):
In PowerShell (Windows):

PowerShell
docker run --rm -v "${PWD}/resultados:/app/resultados" simulador-baterias
In Bash (Mac/Linux):

Bash
docker run --rm -v $(pwd)/resultados:/app/resultados simulador-baterias
(Note: If you want Docker to run the Streamlit web application, make sure to modify the Dockerfile to expose port 8501 and change the ENTRYPOINT to ["streamlit", "run", "appstream.py"], and then run docker run -p 8501:8501 simulador-baterias).

💼 Use Case (Sales Pitch)
This software allows you to debunk inflated simulations from competitors. By adjusting the pricing table within the application (e.g., lowering the Off-peak price to 0.05 € to simulate an indexed contract), the simulator demonstrates how a more affordable and correctly sized battery (100kWh/50kW) can offer a return on investment of 6 to 7 years, vastly outperforming proposals with oversized batteries that rely on hidden tariff conditions to show profitability.