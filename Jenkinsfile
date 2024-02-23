pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.9'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install dependencies') {
            steps {
                script {
                    sh "python${PYTHON_VERSION} -m pip install -r requirements.txt"
                }
            }
        }

        stage('Run tests') {
            steps {
                script {
                    sh "python${PYTHON_VERSION} -m pytest"
                }
            }
        }

        stage('Build Docker image') {
            steps {
                script {
                    sh "docker build -t aggregator_app:latest ."
                }
            }
        }

        stage('Push Docker image') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
                        sh "docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD"
                    }
                    sh "docker push your-docker-username/your-repo-name:latest"
                }
            }
        }

        stage('Deploy') {
            steps {
                // Cloud API will be deployed here
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded!'
        }

        failure {
            echo 'Pipeline failed!'
        }
    }
}
