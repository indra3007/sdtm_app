#!/usr/bin/env python3

"""
Demo: Multiple Workflow Tabs - SDTM Domain-Based Processing
Demonstrates the new tabbed workflow interface for handling multiple SDTM domains simultaneously.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def demo_multiple_workflows():
    """Demo the multiple workflow tabs functionality."""
    
    print("🎯 SDTM Multi-Workflow Demo")
    print("=" * 60)
    
    print("\n📊 NEW FEATURE: Multiple Workflow Tabs")
    print("-" * 40)
    print("✅ Create separate workflows for different SDTM domains")
    print("✅ Work on AE, DM, VS, LB data simultaneously")
    print("✅ Each tab maintains its own flow and connections")
    print("✅ Auto-save and restore individual workflows")
    print("✅ Domain-specific icons and naming")
    
    print("\n🔧 How to Use Multiple Workflows:")
    print("-" * 40)
    print("1. 📊 Click 'New Workflow' button in toolbar")
    print("2. ✏️ Enter workflow name (e.g., 'AE Analysis', 'Demographics')")
    print("3. 🎨 Domain icons auto-assigned based on name:")
    
    domain_examples = {
        'AE Analysis': '⚡ (Adverse Events)',
        'Demographics': '👤 (Demographics)', 
        'Vital Signs': '💓 (Vital Signs)',
        'Laboratory Data': '🧪 (Lab Results)',
        'Concomitant Medications': '💊 (Medications)',
        'Medical History': '📋 (Medical History)',
        'Exposure': '💉 (Drug Exposure)',
        'Disposition': '📊 (Study Status)',
        'Questionnaires': '❓ (QS Domain)'
    }
    
    for name, icon_desc in domain_examples.items():
        print(f"   • '{name}' → {icon_desc}")
    
    print("\n🔄 Workflow Management Features:")
    print("-" * 40)
    print("📋 File Menu → Workflows:")
    print("   • 📊 New Workflow (Ctrl+T)")
    print("   • 📋 Duplicate Current Workflow (Ctrl+Shift+D)")
    print("   • ✏️ Rename Current Workflow")
    print("   • ❌ Close Current Workflow (Ctrl+W)")
    print("   • 💾 Save All Workflows (Ctrl+Shift+A)")
    
    print("\n🎨 Tab Features:")
    print("-" * 40)
    print("✅ Closable tabs (X button)")
    print("✅ Movable tabs (drag to reorder)")
    print("✅ Tooltips with workflow details")
    print("✅ Modified indicator (*) for unsaved changes")
    print("✅ Auto-save confirmation before closing")
    print("✅ Cannot close the last remaining tab")
    
    print("\n🔧 Technical Benefits:")
    print("-" * 40)
    print("✅ Each workflow has its own:")
    print("   • Flow Canvas with nodes and connections")
    print("   • Execution Engine for data processing")
    print("   • Property Panel state")
    print("   • Data Viewer context")
    print("   • File save/load functionality")
    
    print("\n📈 Use Cases:")
    print("-" * 40)
    print("🎯 Scenario 1: Multi-Domain Study Processing")
    print("   • Tab 1: '⚡ AE Analysis' - Adverse event processing")
    print("   • Tab 2: '👤 Demographics' - Subject demographics")
    print("   • Tab 3: '🧪 Lab Results' - Laboratory data transformation")
    print("   • Tab 4: '💓 Vital Signs' - VS domain processing")
    
    print("\n🎯 Scenario 2: Development vs Production")
    print("   • Tab 1: '🔧 Development Flow' - Testing new transformations")
    print("   • Tab 2: '✅ Production Flow' - Validated production workflow")
    print("   • Tab 3: '📊 QC Review' - Quality control validation")
    
    print("\n🎯 Scenario 3: Comparative Analysis")
    print("   • Tab 1: '📈 Method A' - First approach to data processing")
    print("   • Tab 2: '📊 Method B' - Alternative processing method")
    print("   • Tab 3: '🔍 Results Comparison' - Side-by-side evaluation")
    
    print("\n⚡ Quick Start Guide:")
    print("-" * 40)
    print("1. Launch SDTM Flow Builder")
    print("2. Load your SDTM specifications (📋 SDTM Specs button)")
    print("3. Click '📊 New Workflow' → Enter 'AE Analysis'")
    print("4. Drag nodes to build your AE processing flow")
    print("5. Click '📊 New Workflow' → Enter 'Demographics'")
    print("6. Build your DM domain processing in the new tab")
    print("7. Switch between tabs to work on different domains")
    print("8. Use 'Save All Workflows' to save everything at once")
    
    print("\n🔄 Migration from Single Workflow:")
    print("-" * 40)
    print("✅ Existing single workflows continue to work normally")
    print("✅ First tab shows as 'Workflow 1' by default")
    print("✅ Use 'Rename Current Workflow' to give it a proper name")
    print("✅ All existing functionality preserved and enhanced")
    
    print("\n🎉 Benefits Summary:")
    print("-" * 40)
    print("✅ Increased Productivity: Work on multiple domains simultaneously")
    print("✅ Better Organization: Domain-specific tabs with icons")
    print("✅ Reduced Context Switching: Keep all workflows open")
    print("✅ Enhanced Workflow Management: Save, rename, duplicate tabs")
    print("✅ Improved User Experience: Modern tabbed interface")
    print("✅ Scalable Solution: Support for unlimited workflows")
    
    print("\n" + "=" * 60)
    print("🚀 Ready to use Multiple Workflow Tabs!")
    print("Launch the application and click '📊 New Workflow' to start!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = demo_multiple_workflows()
        if success:
            print("\n🎉 Demo completed successfully!")
        else:
            print("\n❌ Demo failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Demo error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)