#!/usr/bin/python


## Imports
import sys
import json
import urllib
import jenkins
import argparse
import feedparser
from jinja2 import Template


## Parse args
parser = argparse.ArgumentParser(description='Jenkins configurator for Rsnapshot')
parser.add_argument('--host',                  action="store",      dest="host",        required=True,                   help='Host')
parser.add_argument('--jenkins',  '-j',        action="store",      dest="jenkinshost", default='http://localhost:8080', help='Jenkins Host')
parser.add_argument('--username', '-u',        action="store",      dest="username",    default=None,                    help='Jenkins Username')
parser.add_argument('--password', '-p',        action="store",      dest="password",    default=None,                    help='Jenkins Password')
parser.add_argument('--delete-all-jobs',       action="store_true", dest="delete",      default=False,                  help='Deletes all jobs in Jenkins')
parser.add_argument('--snapshot-root', '-r',   action="store",      dest="root",        required=True,                   help='Rsnapshot Root')
parser.add_argument('--snapshot-user',         action="store",      dest="user",        default='root',                  help='Rsnapshot User')
parser.add_argument('--snapshot-backups','-b', action="store",      dest="directory",   required=True,                   help='Rsnapshot Backups Folder',  nargs='*')
parser.add_argument('--snapshot-preexec',      action="store",      dest="preexec",     default=False,                   help='Rsnapshot Preexec Command')
args = parser.parse_args()

defaults = {
  'host':args.host,
  'description':'Rsnapshot backup job',
  'config':{'file':'/tmp/rsnapshot-%s'%(args.host)},
  'root':args.root,
  'user':args.user,
  'preexec':args.preexec,
  'directory':args.directory,
}

createjobs = '''
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description>Use this to add per-host backup jobs.</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>Host</name>
          <description>Resolvable hostname or IP of host to be backed up.</description>
          <defaultValue></defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>Directories</name>
          <description>Space delimited list of directories to backup on the remote host.</description>
          <defaultValue>/home/ /root/ /var/ /etc/ /opt/</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>PreExec</name>
          <description>Command to execute prior to backup</description>
          <defaultValue></defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>#!/bin/bash
Root=/home/backups/rsnapshoot/default
if [ ! -d &quot;${Root}&quot; ]; then mkdir -p &quot;${Root}&quot;; fi
gen-rsnapshot-jobs --host ${Host} --snapshot-root=${Root} --snapshot-preexec ${PreExec} --snapshot-backups ${Directories} || gen-rsnapshot-jobs --host ${Host} --snapshot-root=${Root} --snapshot-backups ${Directories} </command>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>
'''

sshcopyid = '''
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>Host</name>
          <description>Hostname or IP address of host to be backed up.</description>
          <defaultValue>localhost</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>User</name>
          <description>Username of backup user.</description>
          <defaultValue>root</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.PasswordParameterDefinition>
          <name>Password</name>
          <description></description>
          <defaultValue>3yB+dHsDzI3Q0fx+x7MoAQ==</defaultValue>
        </hudson.model.PasswordParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>#!/bin/bash
exitcode
/bin/sshpass -p ${Password} ssh ${Host} -l ${USER} -o StrictHostKeyChecking=no hostname
exitcode=$(( $exitcode + $? ))
/bin/sshpass -p ${Password} ssh-copy-id ${USER}@${Host}
exitcode=$(( $exitcode + $? ))
if [ ! &quot;$?&quot; == &quot;0&quot; ]; then
  echo &quot;y&quot; | ssh-keygen -t rsa -N &quot;&quot; -f ~/.ssh/id_rsa
  exitcode=$(( $exitcode + $? ))
fi
exit ${exitcode}</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>
'''



## Delete all jobs in jenkins
if args.delete:
  j = jenkins.Jenkins(args.jenkinshost, args.username, args.password)
  for i in j.get_jobs():
    print('Deleting "%s"'%(i['name']))
    j.delete_job(i['name'])
  sys.exit(0)


## Rsnapshot template
backup = defaults.copy()
with open('/etc/gen-rsnapshot-jobs/rsnapshot-config.jinja2','r') as f: configtext = f.read()
configtemplate = Template(configtext)
config = configtemplate.render(backup=backup)
backup['config']['text'] = config.replace('\n\n','\n').replace('\n\n','\n')
print backup['config']['text']


## Create each schedule
schedules = [
  {"name":"hourly", "cron":"@hourly"},
  {"name":"daily",  "cron":"@daily"},
  {"name":"monthly","cron":"@monthly"},
]
for schedule in schedules:


  ## Defaults
  backup = defaults.copy()
  backup['cron'] = schedule['cron']
  backup['frequency'] = schedule['name']
  backup['title'] = 'Rsnapshot - %s - %s'%(backup['host'],backup['frequency'])


  ## Job template
  with open('/etc/gen-rsnapshot-jobs/jenkins-job.xml.jinja2','r') as f: xmltext = f.read()
  xmltemplate = Template(xmltext)
  xml = xmltemplate.render(backup=backup)


  ## Setup Job
  j = jenkins.Jenkins(args.jenkinshost, args.username, args.password)
  if j.job_exists(backup['title']):
    j.reconfig_job(backup['title'], xml)
  else:
    j.create_job(backup['title'], xml)



## Ensure setup jobs exist
title = '1 - Create Backup Jobs'
j = jenkins.Jenkins(args.jenkinshost, args.username, args.password)
if j.job_exists(title):
  j.delete_job(title)
j.create_job(title, createjobs)


## Ensure setup jobs exist
title = '2 - Deploy SSH Key'
j = jenkins.Jenkins(args.jenkinshost, args.username, args.password)
if j.job_exists(title):
  j.delete_job(title)
j.create_job(title, sshcopyid)



## Show current jobs and status
print('\nBackup Jobs\n===========')
jobs = json.loads(urllib.urlopen('%s/api/json'%(args.jenkinshost)).read())['jobs']
for i in jobs:
  if 'Rsnapshot' in i['name']:
    print(i['name'].replace('broken','failed').replace('build','backup').replace('Rsnapshot','').replace(' - ','\t'))
print('\n\nLatest Runs\n===========')
d = feedparser.parse('%s/rssLatest'%(args.jenkinshost))
for i in d['entries']:
  if 'Rsnapshot' in i['title']:
    print(i['title'].replace('broken','failed').replace('build','backup').replace('Rsnapshot','').replace(' - ','\t'))
print('\n\n')





