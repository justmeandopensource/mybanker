pipeline {
  agent any
  stages {
    stage('greet user') {
      steps {
        input(message: 'Enter your name', id: 'user', ok: 'Continue')
        echo 'Welcome ${user}'
      }
    }
  }
}