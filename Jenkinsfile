pipeline {
    agent any

    environment {
        IMAGE_NAME = "securedev-app"
        CONTAINER_NAME = "securedev-container"
        PORT = "5000"
    }

    stages {
        stage('Construcción (Build)') {
            steps {
                echo 'Fase de Construcción: Empaquetando la aplicación...'
                script {
                    sh 'docker build -t ${IMAGE_NAME}:latest .'
                }
            }
        }

        stage('Pruebas Automatizadas de Seguridad (DAST - OWASP ZAP)') {
            steps {
                echo 'Fase de Pruebas: Iniciando escaneo dinámico con OWASP ZAP...'
                script {
                    // 1. Limpieza preventiva
                    sh 'docker rm -f test-securedev-container || true'
                    sh 'docker rm -f zap-scanner || true'
                    
                    // 2. Levantar la aplicación temporal para ser atacada
                    sh 'docker run -d -p 5050:${PORT} --name test-securedev-container ${IMAGE_NAME}:latest'
                    
                    // Pausa de 10 segundos para asegurar que Flask encendió completamente
                    sleep 10
                    
                    // 3. Obtener IP interna y Lanzar ataque ZAP (Baseline Scan) usando la imagen oficial de GHCR
                    // NOTA: Usamos || true al final para que el pipeline no falle de inmediato si ZAP encuentra algo.
                    sh """
                    TARGET_IP=\$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' test-securedev-container)
                    echo "Atacando objetivo en http://\$TARGET_IP:5000"
                    
                    docker run --name zap-scanner -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t http://\$TARGET_IP:5000 -r zap_report.html || true
                    """
                    
                    // 4. Extraer el reporte de seguridad desde el contenedor ZAP al Jenkins
                    sh 'docker cp zap-scanner:/zap/wrk/zap_report.html ./zap_report.html || true'
                    
                    // 5. Limpieza post-ataque
                    sh 'docker rm -f zap-scanner || true'
                    sh 'docker rm -f test-securedev-container || true'
                }
            }
        }

        stage('Despliegue (Deploy)') {
            steps {
                echo 'Fase de Despliegue: Levantando la aplicación en Producción...'
                script {
                    sh 'docker rm -f ${CONTAINER_NAME} || true'
                    sh 'docker run -d -p ${PORT}:${PORT} --name ${CONTAINER_NAME} ${IMAGE_NAME}:latest'
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline finalizado. Generando registros de trazabilidad y reportes...'
            // ESTO ES CLAVE: Guarda el archivo HTML en la interfaz de Jenkins
            archiveArtifacts artifacts: 'zap_report.html', allowEmptyArchive: true
        }
        success {
            echo '¡Despliegue exitoso!'
        }
        failure {
            echo '¡Fallo en el pipeline! Revisa los logs.'
        }
    }
}
