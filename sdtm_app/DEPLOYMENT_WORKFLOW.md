# SDTM App Development & Production Workflow

## 📋 Branch Structure Overview

```
📂 Repository: indra3007/sdtm_app
├── 🚀 main (Production)          # Stable, production-ready code
├── 🔧 dev (Development)          # Latest stable development code
└── 🌟 feature/* (Features)       # Individual feature development
```

## 🔄 Development Workflow

### 1. **Development Phase (dev branch)**
```bash
# Switch to dev branch for new development
git checkout dev

# Make your changes and test thoroughly
# Run the application: python src/main.py

# Commit changes
git add .
git commit -m "feat: add new feature description"
git push origin dev
```

### 2. **Feature Development (feature branches)**
```bash
# Create feature branch from dev
git checkout dev
git checkout -b feature/new-feature-name

# Develop and test the feature
# Commit changes
git add .
git commit -m "feat: implement new feature"
git push origin feature/new-feature-name

# Merge back to dev when ready
git checkout dev
git merge feature/new-feature-name --no-edit
git push origin dev
```

### 3. **Production Deployment (main branch)**
```bash
# When dev is stable and tested, promote to production
git checkout main
git merge dev --no-edit
git push origin main
```

## 🎯 Current Branch Status

| Branch | Purpose | Status | Last Updated |
|--------|---------|--------|--------------|
| `main` | 🚀 **Production** | ✅ Stable | Latest with property panel fixes |
| `dev` | 🔧 **Development** | ✅ Active | Latest with property panel fixes |
| `feature/property-panel-fixes` | 🌟 **Feature** | ✅ Merged | Property panel styling fixes |

## 🛡️ Quality Gates

### Before Merging to Dev:
- [ ] Application runs without crashes
- [ ] All major features work correctly
- [ ] No console errors during normal operation
- [ ] Code follows project conventions

### Before Promoting to Main (Production):
- [ ] Dev branch is thoroughly tested
- [ ] Application has been run end-to-end
- [ ] All workflows load and execute correctly
- [ ] Property panels display correctly for all node types
- [ ] Data viewer functions properly

## 📁 Directory Structure

```
sdtm_app/
├── src/                          # Core application code
│   ├── ui/                       # User interface components
│   │   ├── property_panel.py     # Node property panels (latest fixes)
│   │   ├── flow_canvas.py        # Workflow canvas
│   │   ├── data_viewer.py        # Data display
│   │   └── main_window.py        # Main application window
│   ├── data/                     # Data processing
│   └── nodes/                    # Node implementations
├── projects/                     # Sample projects and workflows
├── raw/                          # Sample datasets
├── requirements.txt              # Python dependencies
└── README.md                     # Project documentation
```

## 🚀 Quick Start Commands

### Development Environment:
```bash
# Clone and setup
git clone https://github.com/indra3007/sdtm_app.git
cd sdtm_app
pip install -r requirements.txt

# Switch to dev for new development
git checkout dev

# Run the application
python src/main.py
```

### Production Deployment:
```bash
# Use main branch
git checkout main

# Run production version
python src/main.py
```

## 🔧 Key Features Implemented

### ✅ Property Panel Fixes (Latest)
- **Column Keep/Drop**: Consistent 🚀 Actions styling
- **Expression Node**: Maintains existing rocket emoji styling  
- **Domain Node**: Fixed RuntimeError crashes with proper widget lifecycle
- **All Nodes**: Consistent action section styling across the application

### ✅ Version Control Setup
- **Clean Repository**: Only essential files, no test/debug clutter
- **Proper .gitignore**: Excludes cache files, test files, and development artifacts
- **Branch Protection**: Separate dev/prod environments

## 📝 Development Guidelines

### Code Quality:
1. **Test Locally**: Always run `python src/main.py` before committing
2. **Clean Commits**: Use descriptive commit messages
3. **Small Changes**: Keep commits focused and atomic
4. **No Debug Code**: Remove debug files and test scripts before committing

### File Management:
- **Core Files Only**: Only commit essential application files
- **Use .gitignore**: Let git ignore temporary and test files automatically
- **Clean Workspace**: Remove backup files (*_backup.py, *_broken.py)

## 🎯 Next Development Priorities

1. **Performance**: Optimize workflow execution for large datasets
2. **Error Handling**: Improve user experience with better error messages  
3. **Documentation**: Add inline code documentation
4. **Testing**: Implement automated testing framework
5. **Features**: Add new node types and transformations

## 🆘 Troubleshooting

### Common Issues:
- **RuntimeError with QVBoxLayout**: Fixed in property_panel.py
- **Missing rocket symbols**: Fixed in action sections
- **Canvas crashes**: Fixed widget lifecycle management

### Quick Fixes:
```bash
# Reset to stable dev
git checkout dev
git reset --hard origin/dev

# Reset to stable production
git checkout main  
git reset --hard origin/main
```

---

📞 **Support**: Use GitHub Issues for bug reports and feature requests
🔄 **Updates**: This workflow will be updated as the project evolves