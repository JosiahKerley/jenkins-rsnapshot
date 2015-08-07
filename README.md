# jenkins-rsnapshot
Tool that allows you to use jenkins as a backup server.  This tool generates rsnapshot configs, jenkins jobs, and other tools.

## Usage:
```
usage: gen-rsnapshot-jobs [-h] --host HOST [--jenkins JENKINSHOST]
                          [--username USERNAME] [--password PASSWORD]
                          [--delete-all-jobs] --snapshot-root ROOT
                          [--snapshot-user USER] --snapshot-backups
                          [DIRECTORY [DIRECTORY ...]]
                          [--snapshot-preexec PREEXEC]

Jenkins configurator for Rsnapshot

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           Host
  --jenkins JENKINSHOST, -j JENKINSHOST
                        Jenkins Host
  --username USERNAME, -u USERNAME
                        Jenkins Username
  --password PASSWORD, -p PASSWORD
                        Jenkins Password
  --delete-all-jobs     Deletes all jobs in Jenkins
  --snapshot-root ROOT, -r ROOT
                        Rsnapshot Root
  --snapshot-user USER  Rsnapshot User
  --snapshot-backups [DIRECTORY [DIRECTORY ...]], -b [DIRECTORY [DIRECTORY ...]]
                        Rsnapshot Backups Folder
  --snapshot-preexec PREEXEC
                        Rsnapshot Preexec Command
```
