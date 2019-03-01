#!groovy

#!groovy

ansiColor('xterm') {
  node('ops-jenkins') {
    ws("pathman") {
      checkout scm

      def job_name = env.JOB_NAME.tokenize("/")[1]
      def authorName  = sh(returnStdout: true, script: 'git --no-pager show --format="%an" --no-patch')
      def serviceName = env.JOB_NAME.tokenize("/")[1]
      def isMaster = env.BRANCH_NAME == "master"
      def commitHash  = sh(returnStdout: true, script: 'git rev-parse HEAD | cut -c-7').trim()
      def version    = "${env.BUILD_NUMBER}-${commitHash}"
      def imageTag = "${env.BUILD_NUMBER}-${commitHash}"

    try {
      stage("Test") {
        sh """make test"""
      }

      if(isMaster) {
        stage("Build Image") {
          sh "IMAGE_TAG=${imageTag} make build"
          sh "IMAGE_TAG=latest make build"
        }
        stage("Push Image") {
          sh "IMAGE_TAG=${imageTag} make push"
          sh "IMAGE_TAG=latest make push"
        }
      }
    } catch (e) {
      slackSend(color: '#b20000', message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}) by ${authorName}")
      throw e
    }
    slackSend(color: '#006600', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}) by ${authorName}")
    }
  }
}
