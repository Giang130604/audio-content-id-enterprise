# GitHub Setup

Target remote:

```text
https://github.com/Giang130604/audio-content-id-enterprise.git
```

This environment does not currently have GitHub CLI (`gh`) installed, and the
available GitHub connector can write to existing repositories but cannot create
new repositories. Create the repository once, then push the local commit.

## Create the Private Repository

1. Open https://github.com/new.
2. Set owner to `Giang130604`.
3. Set repository name to `audio-content-id-enterprise`.
4. Set visibility to `Private`.
5. Do not initialize with README, `.gitignore`, or license because this local
   repo already contains the initial commit.

## Push Local Code

```powershell
cd "D:\Copyright Strike Tool"
git push -u origin main
```

If Git asks for authentication, sign in with Git Credential Manager or install
GitHub CLI and run:

```powershell
gh auth login
git push -u origin main
```
