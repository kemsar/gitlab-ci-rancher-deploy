```
Usage: ranchertool [OPTIONS]

  Performs an operation on a Rancher service specified on the command
  line

Options:
  --rancher-url TEXT              The URL for your Rancher server.  [required]
  --rancher-key TEXT              The environment or account API Access Key.
                                  [required]

  --rancher-secret TEXT           The secret for the API Access Key.
                                  [required]

  --stack TEXT                    The name of the target stack in Rancher.
                                  Defaults to the name of the GitLab project
                                  group as defined in the CI_PROJECT_NAMESPACE
                                  environment variable.  [required]

  --service TEXT                  The name of the service in Rancher to
                                  upgrade/create. Defaults to the name of the
                                  GitLab project as defined in the
                                  CI_PROJECT_NAME environment variable.
                                  [required]

  --api-version [v1|v2-beta]      The API version to use. Rancher versions < 2
                                  have API versions v1 and v2-beta. The
                                  default is v2-beta.

  --environment TEXT              The name of the Rancher environment to
                                  operate in. In the Rancher API, this is
                                  called 'project'.This is only required if
                                  you are using an account API key instead of
                                  an environment API key.

  --start-before-stopping / --no-start-before-stopping
                                  Controls whether or not new containers
                                  should be started before the old ones are
                                  stopped. Defaults to --no-start-before-
                                  stopping.

  --batch-size INTEGER            Sets the number of containers to upgrade
                                  simultaneously. Defaults to 1.

  --batch-interval INTEGER        Sets the number of seconds to wait between
                                  batches. Defaults to 2 seconds.

  --timeout INTEGER               Sets how many seconds to wait for Rancher to
                                  finish processing before assuming something
                                  went wrong. Defaults to 300 seconds (5
                                  mins). This setting is ignored if --no-wait
                                  is used.

  --wait / --no-wait              Sets whether or not to wait for Rancher to
                                  finish processing the request. Defaults to
                                  --wait. If --no-wait is used, --timeout is
                                  ignored.

  --rollback / --no-rollback      Sets whether or not to roll back changes if
                                  an error occurs. Defaults to --no-rollback.
                                  Only valid in conjunction with --wait.

  --image TEXT                    If specified, replaces the current service's
                                  image (and :tag) with the one specified.

  --finish / --no-finish          Sets whether or not to finish an upgrade
                                  when it completes. Defaults to --finish.

  --sidekicks / --no-sidekicks    Sets whether or not to upgrade service
                                  sidekicks at the same time. Defaults to
                                  --no-sidekicks.

  --new-sidekick-image <TEXT TEXT>...
                                  If specified, replaces the existing sidekick
                                  image (and :tag) with the specified one.
                                  This can be defined more than once to
                                  upgrade multiple sidekicks. Example: '--new-
                                  sidekick-image <sidekick-name> <new-image>'

  --create-stack / --no-create-stack
                                  Sets whether or not to create the targeted
                                  Rancher stack if it doesn't exist. Defaults
                                  to --no-create-stack.

  --create-service / --no-create-service
                                  Sets whether or not to create the targeted
                                  Rancher service if it doesn't exist.
                                  Defaults to --no-create-service.

  --labels TEXT                   If specified, labels will be added to the
                                  service. Labels to be added should be
                                  provided as a comma-delimited list of
                                  <label-name>=<label-value> pairs.

  --label <TEXT TEXT>...          Another way to add labels to a service. This
                                  one can be defined multiple times. Example:
                                  '--label label1 value1 --label label2
                                  value2'

  --variables TEXT                If specified, adds the passed list of
                                  environment variables to the service. The
                                  list of variables should be a pipe-delimited
                                  (|) list of <key>=<value> pairs. Example: '
                                  --variables var1=val1|var2=val2|var3=val3'.

  --variable <TEXT TEXT>...       Another way to add environment variables to
                                  a service. See --label for syntax.

  --service-links TEXT            If specified, adds the provided list of
                                  service links to the service. See --labels
                                  for syntax. Example: '--service-links
                                  <local-name1>=<target-name1>,<local-
                                  name2>=<target-name2>'. Target service name
                                  should be in the format of
                                  '<stack>/<service>'.

  --service-link <TEXT TEXT>...   Another way to add service links to a
                                  service. See --label for syntax.

  --log-level [TRACE|DEBUG|INFO|WARN|ERROR|FATAL|SILENT]
                                  Determines how much information is written
                                  to the console. ranchertool will first check to
                                  see if this argument is provided. If not, it
                                  will check for a 'LOG_LEVEL' environment
                                  variable. If the 'LOG_LEVEL' environment
                                  variable isn't set, it will default to INFO.

  --debug-http / --no-debug-http  Sets whether or not to enable debug mode for
                                  HTTP requests. Defaults to --no-debug-http.

  --ssl-verify / --no-ssl-verify  Sets whether or not to perform certificate
                                  checks. Defaults to --ssl-verify. Use this
                                  to allow connecting to a HTTPS Rancher
                                  server using an self-signed certificate

  --help                          Show this message and exit.
```
