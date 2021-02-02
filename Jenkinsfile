#!groovy
/***
 *  CI Pipeline for Conda based Python Application
 *
 *  Author: Sören Räuchle
 */

@Library('dreipc-common@develop') _
import de.dreipc.jenkins.python.*
import de.dreipc.jenkins.*

new PythonServicePipeline(this)
  .build()
  .copyFrontend(
        sourceBuildJobName: 'q8r/q8r%2Fservice%2Fasset%2Fdocument%2Fnamed-entities-web/master',
        zipFileNameToCopy: 'named-entities-web.zip',
        targetDir: "named_entities_service/static")
  .dockerize(imageName: 'nexus.3pc.de/q8r/asset/document/named-entities-service')
  .onSuccessNotifyChannels(['#tqurator-builds'])
  .onErrorNotifyChannels(['@nbabai'])
  .execute()