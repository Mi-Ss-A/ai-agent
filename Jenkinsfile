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

        stage('Delete Older Images') {
            steps {
                script {
                    sh '''
                    # 현재 빌드된 이미지와 직전 버전 태그 계산
                    IMAGE_NAME="${IMAGE_NAME}"
                    CURRENT_TAG="${TAG}"
                    PREVIOUS_TAG="test-$(( ${BUILD_NUMBER} - 1 ))"

                    echo "현재 유지할 이미지 태그: ${CURRENT_TAG}, ${PREVIOUS_TAG}"

                    # 모든 이미지 목록 가져오기
                    docker images --format '{{.Repository}}:{{.Tag}}' | grep "$IMAGE_NAME" | while read -r IMAGE; do
                        # 유지할 태그인지 확인 (POSIX 호환 방식으로 수정)
                        if [ "$IMAGE" = "${IMAGE_NAME}:${CURRENT_TAG}" ] || [ "$IMAGE" = "${IMAGE_NAME}:${PREVIOUS_TAG}" ]; then
                            echo "유지할 이미지: $IMAGE"
                        else
                            echo "삭제할 이미지: $IMAGE"
                            docker rmi -f "$IMAGE" || echo "이미지 삭제 실패: $IMAGE"
                        fi
                    done
                    '''
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
