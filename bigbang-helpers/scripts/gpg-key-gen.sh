#!/bin/bash

# quickly generates a key with name $1

echo "Creating gpg key for ${1}"

gpg --quick-generate-key --batch --passphrase '' ${1}
fingerPrint=$(gpg -K ${1} | sed -e 's/ *//;2q;d;')

gpg --quick-add-key --batch --passphrase '' "${fingerPrint}" rsa4096 encr

