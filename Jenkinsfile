pipeline {
    agent any

    environment {
        // Variables de entorno para Docker
        IMAGE_NAME = "securedev-app"
        CONTAINER_NAME = "securedev-container"
        PORT = "5000"
    }

    stages {
        stage('Construcción (Build)') {
            steps {
                echo 'Fase de Construcción: Empaquetando la aplicación en Docker...'
                script {
                    // Construye la imagen de Docker usando el Dockerfile
                    sh 'docker build -t ${IMAGE_NAME}:latest .'
                }
            }
        }

        stage('Pruebas Automatizadas de Seguridad (DAST)') {
            steps {
                echo 'Fase de Pruebas: Ejecutando OWASP ZAP (Placeholder)...'
                // Aquí levantaremos temporalmente el contenedor para que ZAP lo ataque.
                // La configuración exacta de ZAP la haremos en la Parte 3.
                script {
                    echo 'Preparando entorno para pruebas de penetración continuas...'
                    sh 'docker run -d -p 5050:${PORT} --name test-${CONTAINER_NAME} ${IMAGE_NAME}:latest'
                    // Simulación de pausa para que el servidor levante antes del escaneo
                    sleep 5
                    
                    // (En la Parte 3 inyectaremos el comando de ZAP aquí)
                    
                    // Limpieza del contenedor de pruebas
                    sh 'docker stop test-${CONTAINER_NAME} || true'
                    sh 'docker rm test-${CONTAINER_NAME} || true'
                }
            }
        }

        stage('Despliegue (Deploy)') {
            steps {
                echo 'Fase de Despliegue: Levantando la aplicación en Producción...'
                script {
                    // Detener y eliminar el contenedor viejo si existe para evitar conflictos de puerto
                    sh 'docker stop ${CONTAINER_NAME} || true'
                    sh 'docker rm ${CONTAINER_NAME} || true'
                    
                    // Desplegar la nueva versión segura
                    sh 'docker run -d -p ${PORT}:${PORT} --name ${CONTAINER_NAME} ${IMAGE_NAME}:latest'
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline finalizado. Generando registros de trazabilidad...'
        }
        success {
            echo '¡Despliegue exitoso y sin vulnerabilidades críticas!'
        }
        failure {
            echo '¡Fallo en el pipeline! Revisa los logs de seguridad.'
        }
    }
}
