
To supply values for the AWS keys in the manifest.yml, supply a vars.yml file
with the appropriate values -- see https://docs.cloudfoundry.org/devguide/deploy-apps/manifest-attributes.html

use "cf push --vars-file /PATH/vars.yml" to use the vars file
(note that vars.yml is in the .gitignore, to reduce risk)
