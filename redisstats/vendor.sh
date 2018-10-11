[[ ! -d vendor ]] && mkdir vendor
pip download --dest vendor -r requirements.txt --no-binary :all:
