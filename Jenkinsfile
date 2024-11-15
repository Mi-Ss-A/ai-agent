pipeline {
    agent any

    environment {
        IMAGE_NAME = "been980804/wibee-agent"
        DEPLOYMENT_REPO = 'https://github.com/Mi-Ss-A/wibeechat-argocd-config'
        GIT_CREDENTIALS = credentials('git-token')
        TAG = "test-${BUILD_NUMBER}" // Jenkins 빌드 넘버로 자동 증가되는 태그
        DOCKER_IMAGE = "${IMAGE_NAME}:${TAG}"
    }

    stages {
        stage('Checkout Source') {
            steps {
                script {
                    echo "Checking out source code..."
                }
                checkout scm
            }
        }

        stage('Prepare .env file') {
            steps {
                script {
                    echo "Preparing .env file..."
                    def envContent = credentials('env-file-credentials') // Jenkins에 저장된 .env 파일 내용
                    writeFile file: '.env', text: envContent
                    echo ".env file created successfully."
                }
            }
        }

        stage('Build Docker image & Push') {
            steps {
                script {
                    echo "Starting Docker build and push process..."
                    try {
                        docker.withRegistry("https://registry.hub.docker.com", 'docker-token') {
                            def app = docker.build("${DOCKER_IMAGE}", "-f Dockerfile .")
                            app.push()
                        }
                        echo "Docker image ${DOCKER_IMAGE} built and pushed successfully."
                    } catch (Exception e) {
                        echo "Error during Docker build or push: ${e.message}"
                        error "Docker build and push failed."
                    }
                }
            }
        }

        stage('Update K8S Manifest') {
            steps {
                dir('k8s-manifest') {
                    script {
                        echo "Cloning Kubernetes manifest repository..."
                        git url: DEPLOYMENT_REPO, branch: 'test', credentialsId: 'git-token'

                        echo "Updating Kubernetes deployment manifest..."
                        sh '''
                        sed -i "s|image: .*$|image: ${DOCKER_IMAGE}|" ai-agent/deployment.yaml
                        git config user.name "hongminyeong"
                        git config user.email "minyung1240@daum.net"
                        git commit -am "Update image to ${DOCKER_IMAGE}"
                        git push https://${GIT_CREDENTIALS_USR}:${GIT_CREDENTIALS_PSW}@github.com/Mi-Ss-A/wibeechat-argocd-config test
                        '''
                        echo "Kubernetes manifest updated and pushed to repository."
                    }
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline execution completed. Cleaning workspace..."
            cleanWs()
        }
        success {
            echo "Pipeline executed successfully."
        }
        failure {
            echo "Pipeline failed. Check logs for details."
        }
    }
}
