# Upload this project to GitHub

This guide is for the ChurnCast project in this folder. It uses Windows PowerShell
commands. If PowerShell says `git` is not recognized, follow the installation
steps below first.

## Install Git for Windows

1. Download Git for Windows from [git-scm.com/download/win](https://git-scm.com/download/win)
   and run the installer.
2. During setup, keep the option that makes Git available from the command line
   (usually labeled **Git from the command line and also from 3rd-party
   software**).
3. Finish the installation, then close and reopen PowerShell (and VS Code if
   its integrated terminal is open).
4. Verify Git is available:

   ```powershell
   git --version
   ```

If you already installed Git but still see “not recognized,” restarting the
terminal often refreshes `PATH`. Otherwise, rerun the installer and ensure its
command-line PATH option is enabled.

## 1. Check the files before uploading

The project already has a root `.gitignore` for Python cache files and
`frontend/.gitignore` for `node_modules`, build output, logs, and the local
`frontend/.env` file. Keep real credentials and private data out of GitHub.
The `.env.example` file is safe to commit as a configuration template.

If you have created other secret or private files, add their paths to the
appropriate `.gitignore` before staging files.

## 2. Create an empty GitHub repository

1. Sign in at [github.com](https://github.com/) and choose **New repository**.
2. Enter a repository name, such as `churncast`.
3. Choose **Public** or **Private**.
4. Do not initialize it with a README, `.gitignore`, or license. This project
   already contains project files, so an empty repository avoids an unrelated
   first-commit history.
5. Select **Create repository** and copy its HTTPS URL. It will look like
   `https://github.com/YOUR-USERNAME/churncast.git`.

## 3. Initialize Git and make the first commit

Open PowerShell in the project root (the folder containing `README.md`), not in
the `frontend` subfolder. From `frontend`, return to the project root with
`Set-Location ..`. Then run:

```powershell
git --version
git init
git branch -M main
git status --short
```

Review the status output. In particular, make sure local `.env` files,
`node_modules`, and build output are not listed. The nested
`frontend/.gitignore` should exclude those frontend-local files.

Stage and commit the project:

```powershell
git add .
git status
git commit -m "Initial project upload"
```

Review `git status` before committing. If Git asks you to set your name and
email, use the identity you want associated with your commits:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Then run the `git commit` command again.

## 4. Connect the GitHub repository and push

Replace the URL below with the HTTPS URL copied from your new GitHub repository:

```powershell
git remote add origin https://github.com/YOUR-USERNAME/churncast.git
git push -u origin main
```

GitHub may open a browser window for authentication. Follow its sign-in prompt;
do not put a password or personal access token directly into the remote URL or
into a project file.

## 5. Verify the upload

Refresh the repository page on GitHub. You should see the project files,
including `README.md`, `frontend`, `data`, and `docs`. You can also check the
configured remote and local status with:

```powershell
git remote -v
git status
```

## Future updates

After editing the project, upload later changes with:

```powershell
git add .
git commit -m "Describe your changes"
git push
```

## Optional: verify the frontend build first

The dashboard's Vite app is in `frontend`. To verify it builds before uploading:

```powershell
Set-Location .\frontend
npm ci
npm run build
Set-Location ..
```

`npm ci` installs from the frontend lockfile. The generated `frontend/dist`
directory is build output and is excluded by `frontend/.gitignore`.
