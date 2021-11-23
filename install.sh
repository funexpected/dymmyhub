#! /bin/bash

TARGET_REPO=$@
SSH_KEY_PATH="$HOME/.ssh/id_rsa"
REPO="funexpected/dymmyhub"
BRANCH="master"
URL="https://raw.githubusercontent.com/$REPO/$BRANCH"
REQUIREMENTS_URL="$URL/requirements.txt"
INSTALLER_URL="$URL/login.py"
DESTINATION_FOLDER="$(osascript -l JavaScript -e 'a=Application.currentApplication();a.includeStandardAdditions=true;a.chooseFolder({withPrompt:"Please select working directory for repo"}).toString()')"
if [ -z "$DESTINATION_FOLDER" ]; then
    echo "No valid destination folder selected"
    exit 1
fi


mkdir -p ~/.dummyhub
cd ~/.dummyhub
python3 -mvenv .venv
source .venv/bin/activate

echo "Fetching install script"
curl -sSL $REQUIREMENTS_URL > requirements.txt
curl -sSL $INSTALLER_URL > login.py

echo "Installing dependencies"
pip install -r requirements.txt >/dev/null 2>&1

echo "Installing developer tools"
xcode-select --install

if [ ! -f "$SSH_KEY_PATH.pub" ]; then
    echo "Generating new ssh key"
    ssh-keygen -t rsa -N "" -C "dummyhub generated" -f $SSH_KEY_PATH
fi

python login.py

# install brew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install git-lfs
git lfs install


if [ -d "$DESTINATION_FOLDER/.git" ]; then
    echo "Using existing project"
else
    echo "git clone git@github.com:$TARGET_REPO.git $DESTINATION_FOLDER"
    git clone git@github.com:$TARGET_REPO.git $DESTINATION_FOLDER
    cd $DESTINATION_FOLDER
    git submodule init
    git submodule update
fi

if [ -f "$DESTINATION_FOLDER/install.sh" ]; then
    cd $DESTINATION_FOLDER
    ./install.sh
fi
