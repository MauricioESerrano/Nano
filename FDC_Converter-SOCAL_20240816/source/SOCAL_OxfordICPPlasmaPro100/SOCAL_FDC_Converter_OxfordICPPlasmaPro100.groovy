properties([
    buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '', numToKeepStr: '10')), 
    disableConcurrentBuilds(), 
    [$class: 'RebuildSettings', autoRebuild: false, rebuildDisabled: false],
    parameters([
        string(defaultValue: 'NA', description: 'Assign Tool ID', name: 'Tool_Id', trim: true),
        string(defaultValue: 'NA', description: 'Assign Chamber ID', name: 'Chamber_Id', trim: true)
    ])
])


pipeline {
    agent any

    stages {
        stage('Git') {
            steps {
                // Get some code from a GitHub repository
                git branch: 'main', url: 'http://10.10.60.247:3000/yupuw/FDC_Converter.git'
            }
        }
        
        stage('Preparation') {
            steps {
                script {
                    BUILD_TRIGGER_BY = currentBuild.getBuildCauses()[0].userId
                    BUILD_NUMBER = currentBuild.getNumber()
                    currentBuild.displayName = "#${BUILD_NUMBER} - ${BUILD_TRIGGER_BY} - ${params.Tool_Id}, ${params.Chamber_Id}"
                }
                sh 'rm -rf box/*'
                sh 'mkdir -p box/input box/logdir box/outdir'
                sh 'cp -L ./*.csv box/input/'
            }
        }
        
        stage('Execution') {
            steps {
                sh 'python3 ./source/SOCAL_OxfordICPPlasmaPro100/FDC_Script_SOCAL_OxfordICPPlasmaPro100.py box/input/ ${Tool_Id} ${Chamber_Id} -outdir box/outdir/ -logdir box/logdir/ -ext csv'
            }
        }
        
        stage('Archive') {
            steps {
                sh 'cd box; tar czf exntrace_files.tar.gz ./outdir/*.exntrace ; zip -qq -r exntrace_files outdir'
                archiveArtifacts artifacts: 'box/exntrace_files.*', followSymlinks: false
                archiveArtifacts artifacts: 'box/logdir//*.*', followSymlinks: false
            }
        }
        
    }
}
