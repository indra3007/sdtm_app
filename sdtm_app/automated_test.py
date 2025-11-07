"""
Automated test to reproduce the data viewer issue
"""
import sys
sys.path.append('src')
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ui.main_window import MainWindow

class AutomatedTest:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.window.show()
        
        # Set up timer to run test steps automatically
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_test_step)
        self.step = 0
        self.timer.start(2000)  # Run every 2 seconds
        
    def run_test_step(self):
        print(f"=== AUTO TEST STEP {self.step} ===")
        
        if self.step == 0:
            print("Step 0: Loading AE_copy workflow...")
            self.load_workflow()
        elif self.step == 1:
            print("Step 1: Clicking Execute button...")
            self.execute_workflow()
        elif self.step == 2:
            print("Step 2: Waiting for execution to complete...")
            pass  # Just wait
        elif self.step == 3:
            print("Step 3: Selecting a data input node...")
            self.select_data_node()
        elif self.step == 4:
            print("Step 4: Test complete!")
            self.timer.stop()
            
        self.step += 1
        
    def load_workflow(self):
        """Load the AE_copy workflow"""
        try:
            # Simulate loading the workflow - this would normally be done through UI
            print("AUTO TEST: Would load workflow here...")
            # For now, just print that we would load it
            return True
        except Exception as e:
            print(f"AUTO TEST: Error loading workflow: {e}")
            return False
            
    def execute_workflow(self):
        """Click the execute button"""
        try:
            execute_button = self.window.execute_button
            if execute_button:
                execute_button.click()
                print("AUTO TEST: Execute button clicked!")
                return True
            else:
                print("AUTO TEST: Execute button not found")
                return False
        except Exception as e:
            print(f"AUTO TEST: Error executing: {e}")
            return False
            
    def select_data_node(self):
        """Select a data input node to test data viewer"""
        try:
            current_canvas = self.window.workflow_tabs.currentWidget()
            if not current_canvas:
                print("AUTO TEST: No canvas available")
                return False
                
            if hasattr(current_canvas, 'nodes') and current_canvas.nodes:
                # Find first node
                first_node = current_canvas.nodes[0]
                print(f"AUTO TEST: Selecting node: {first_node.title}")
                
                # Trigger node selection manually
                self.window.on_node_selected_for_data_view(first_node)
                print("AUTO TEST: Node selection triggered!")
                return True
            else:
                print("AUTO TEST: No nodes found in canvas")
                return False
        except Exception as e:
            print(f"AUTO TEST: Error selecting node: {e}")
            return False
            
    def run(self):
        print("Starting automated data viewer test...")
        print("This will automatically load workflow, execute, and test data viewer")
        return self.app.exec()

if __name__ == "__main__":
    test = AutomatedTest()
    test.run()