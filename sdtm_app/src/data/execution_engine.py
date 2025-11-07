"""
Flow Execution Engine

Handles executing data transformation flows through connected nodes.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
import traceback


class FlowExecutionEngine:
    """Engine for executing data transformation flows."""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.execution_order = []
        self.node_outputs = {}  # Store processed data for each node
        self.last_error = None  # Store the last execution error
        self.failed_nodes = set()  # Track nodes that have failed execution
        self.invalid_nodes = set()  # Track nodes that are invalid due to upstream failures
        self.log_callback = None  # Callback function for logging messages to the UI
        
    def set_log_callback(self, callback):
        """Set a callback function for logging messages to the UI."""
        self.log_callback = callback
        
    def log(self, message):
        """Log a message both to console and UI (if callback is set)."""
        print(message)
        if self.log_callback:
            self.log_callback(message)
            
    def execute_flow(self):
        """Execute the complete flow pipeline."""
        try:
            self.log(f"Starting flow execution...")
            
            # Clear previous failure tracking
            self.clear_failure_tracking()
            
            # CRITICAL FIX: Ensure all nodes have access to the execution engine
            for node in self.canvas.nodes:
                if hasattr(node, 'canvas') and node.canvas:
                    node.canvas.execution_engine = self
            
            # 1. Validate flow
            if not self.validate_flow():
                self.log(f"Flow validation failed")
                return False
                
            # 2. Determine execution order
            self.execution_order = self.calculate_execution_order()
            if not self.execution_order:
                self.log(f"Could not determine execution order - possible circular dependencies")
                return False
                
            self.log(f"Execution order: {[node.title for node in self.execution_order]}")
            
            # 3. Execute nodes in order
            total_nodes = len(self.execution_order)
            successful_nodes = 0
            failed_nodes = 0
            
            for i, node in enumerate(self.execution_order):
                self.log(f"Executing {i+1}/{total_nodes}: {node.title}")
                
                if not self.execute_node(node):
                    failed_nodes += 1
                    self.log(f"Failed to execute node: {node.title}")
                    continue  # Continue to next node instead of breaking
                else:
                    successful_nodes += 1
                    self.log(f"Completed: {node.title}")
                    
            # Final summary
            if failed_nodes == 0:
                self.log(f"Flow execution completed successfully!")
                return True
            else:
                self.log(f"Flow execution completed with errors!")
                return False
                
        except Exception as e:
            error_msg = f"Fatal execution error: {str(e)}"
            self.log(f"{error_msg}")
            import traceback
            traceback.print_exc()
            self.last_error = error_msg
            return False
            self.log(f"{error_msg}")
            import traceback
            traceback.print_exc()
            self.last_error = error_msg
            return False
            
    def execute_node(self, node):
        """Execute a single node and its dependencies."""
        try:
            node.set_execution_status("running", 10)
            
            # Check for different node types - use class name for more reliable detection
            node_class_name = type(node).__name__
            print(f"EXECUTE NODE: {node.title} (class: {node_class_name})")
            
            if hasattr(node, 'included_columns') and hasattr(node, 'excluded_columns'):
                # Column keep/drop node
                success = self.execute_column_keep_drop_node(node)
            elif hasattr(node, 'filename'):
                # Data input node - load data from file
                success = self.execute_data_input_node(node)
            elif node_class_name in ['DomainNode', 'ColumnRenamerNode', 'ExpressionBuilderNode', 
                                   'ConstantValueColumnNode', 'RowFilterNode', 'ConditionalMappingNode']:
                # Known transformation nodes - delegate to specialized execution
                success = self.execute_transformation_node(node)
            elif hasattr(node, 'node_type'):
                # Node with generic node_type attribute
                success = self.execute_typed_node(node)
            else:
                # For other nodes, just pass through input data
                input_data = self.get_node_input_data(node)
                if input_data is not None:
                    # Store using both node object and title for compatibility
                    self.node_outputs[node] = input_data
                    self.node_outputs[node.title] = input_data
                    success = True
                else:
                    print(f"No input data available for {node.title}")
                    success = False
                    
            if success:
                node.set_execution_status("success")
                return True
            else:
                node.set_execution_status("error")
                self.failed_nodes.add(node)
                return False
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error executing node {node.title}: {error_msg}")
            self.last_error = error_msg
            node.set_execution_status("error")
            self.failed_nodes.add(node)
            return False
            
    def execute_column_keep_drop_node(self, node):
        """Execute a column keep/drop node - filter columns based on includes/excludes with robust error handling."""
        try:
            print(f"EXECUTE COLUMN KEEP/DROP: {getattr(node, 'title', 'Unknown Node')}")
            
            # Validate node attributes
            if not hasattr(node, 'included_columns'):
                print(f"❌ Node missing 'included_columns' attribute")
                return False
                
            if not hasattr(node, 'excluded_columns'):
                print(f"❌ Node missing 'excluded_columns' attribute") 
                return False
            
            # Get input data with error handling
            try:
                input_df = self.get_node_input_data(node)
            except Exception as e:
                print(f"❌ Error getting input data: {e}")
                return False
                
            if input_df is None:
                print(f"❌ No input data available for column keep/drop")
                return False
                
            if not hasattr(input_df, 'shape') or not hasattr(input_df, 'columns'):
                print(f"❌ Input data is not a valid DataFrame")
                return False
                
            print(f"✅ Input data shape: {input_df.shape}")
            print(f"✅ Input columns: {list(input_df.columns)}")
            print(f"✅ Included columns: {node.included_columns}")
            
            # Validate that included columns exist in input data
            input_columns = list(input_df.columns)
            valid_included = [col for col in node.included_columns if col in input_columns]
            
            if not valid_included:
                print(f"❌ No valid columns to keep in node: {getattr(node, 'title', 'Unknown Node')}")
                print(f"   Requested columns: {node.included_columns}")
                print(f"   Available columns: {input_columns}")
                return False
            
            # Check for missing columns and warn
            missing_columns = [col for col in node.included_columns if col not in input_columns]
            if missing_columns:
                print(f"⚠️ Warning: Some requested columns not found: {missing_columns}")
                
            # Filter the dataframe to keep only included columns
            try:
                filtered_data = input_df[valid_included].copy()
            except Exception as e:
                print(f"❌ Error filtering DataFrame: {e}")
                return False
            
            print(f"✅ Column keep/drop output: {len(filtered_data)} rows, {len(filtered_data.columns)} columns")
            print(f"✅ Output columns: {list(filtered_data.columns)}")
            
            # Store using both node object and title for compatibility
            try:
                self.node_outputs[node] = filtered_data
                self.node_outputs[getattr(node, 'title', 'Unknown Node')] = filtered_data
                print(f"✅ COLUMN KEEP/DROP SUCCESS: {getattr(node, 'title', 'Unknown Node')}")
            except Exception as e:
                print(f"❌ Error storing output data: {e}")
                return False
            
            return True
            
        except Exception as e:
            error_msg = f"Column Keep/Drop execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False
            
    def execute_data_input_node(self, node):
        """Execute a data input node - load data from file."""
        try:
            print(f"EXECUTE DATA INPUT NODE: {node.title}")
            
            # Check if node has dataframe already loaded
            if hasattr(node, 'dataframe') and node.dataframe is not None:
                print(f"Using pre-loaded dataframe: {node.dataframe.shape}")
                # Store the dataframe in our outputs cache using both node and title
                self.node_outputs[node] = node.dataframe.copy()
                self.node_outputs[node.title] = node.dataframe.copy()
                print(f"DATA INPUT NODE SUCCESS: {node.title}")
                return True
            else:
                print(f"No dataframe loaded for data input node: {node.title}")
                # Try to load data if filename is available
                if hasattr(node, 'filename') and node.filename:
                    print(f"Attempting to load data from filename: {node.filename}")
                    # This would require integration with data manager - for now, return False
                    print(f"Data loading from file not implemented in execution engine")
                return False
                
        except Exception as e:
            error_msg = f"Data input node execution failed: {str(e)}"
            print(f"{error_msg}")
            import traceback
            traceback.print_exc()
            return False

    def execute_typed_node(self, node):
        """Execute a node based on its specific type."""
        try:
            print(f"EXECUTE TYPED NODE: {node.title} (type: {getattr(node, 'node_type', 'unknown')})")
            
            # Get input data first
            input_data = self.get_node_input_data(node)
            if input_data is None:
                print(f"No input data for typed node: {node.title}")
                return False
                
            print(f"TYPED NODE: Input data shape: {input_data.shape}")
            
            # CRITICAL FIX: Ensure the node has access to the execution engine cache
            # This allows the node's get_input_data() method to find cached data
            if hasattr(node, 'canvas') and node.canvas:
                # Make sure execution engine reference is available
                if not hasattr(node.canvas, 'execution_engine'):
                    node.canvas.execution_engine = self
                    
            # Check if the node has an execute method
            if hasattr(node, 'execute') and callable(node.execute):
                try:
                    print(f"Calling node.execute() for {node.title}")
                    result = node.execute()
                    if result:
                        # If the node executed successfully, get output data
                        if hasattr(node, 'output_data') and node.output_data is not None:
                            output_data = node.output_data
                            print(f"TYPED NODE: Got output_data with shape: {output_data.shape}")
                        elif hasattr(node, 'get_output_data') and callable(node.get_output_data):
                            output_data = node.get_output_data()
                            print(f"TYPED NODE: Got data via get_output_data() with shape: {output_data.shape if output_data is not None else 'None'}")
                        else:
                            # Use input data as output if no specific output
                            output_data = input_data
                            print(f"TYPED NODE: Using input data as output")
                            
                        # Store the output data
                        self.node_outputs[node] = output_data
                        self.node_outputs[node.title] = output_data
                        print(f"TYPED NODE SUCCESS: {node.title} - Cached output with shape: {output_data.shape}")
                        return True
                    else:
                        print(f"Node.execute() returned False for {node.title}")
                        return False
                except Exception as e:
                    print(f"Error calling node.execute() for {node.title}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                # No execute method - just pass through the data
                self.node_outputs[node] = input_data
                self.node_outputs[node.title] = input_data
                print(f"TYPED NODE PASSTHROUGH: {node.title}")
                return True
                
        except Exception as e:
            error_msg = f"Typed node execution failed: {str(e)}"
            print(f"{error_msg}")
            import traceback
            traceback.print_exc()
            return False
            
    def execute_transformation_node(self, node):
        """Execute a transformation node (Domain, Renamer, etc.) using the same logic as individual execution."""
        try:
            node_class_name = type(node).__name__
            print(f"EXECUTE TRANSFORMATION NODE: {node.title} (class: {node_class_name})")
            
            # Ensure the node has access to execution engine through canvas
            if hasattr(node, 'canvas') and node.canvas:
                node.canvas.execution_engine = self
            
            # Get input data and make it available to the node
            input_data = self.get_node_input_data(node)
            if input_data is None and node_class_name != 'DataInputNode':
                print(f"No input data for transformation node: {node.title}")
                return False
                
            print(f"TRANSFORMATION NODE: Input data shape: {input_data.shape if input_data is not None else 'None'}")
            
            # Call the node's execute method - this is the same as individual execution
            if hasattr(node, 'execute') and callable(node.execute):
                
                # CRITICAL: Pre-execution validation for ExpressionBuilderNode
                if node_class_name == 'ExpressionBuilderNode':
                    validation_result = self.validate_expression_node_before_execution(node)
                    if not validation_result:
                        print(f"VALIDATION ERROR: {node.title} - Expression validation failed, skipping execution")
                        return False
                
                print(f"Calling {node_class_name}.execute() for {node.title}")
                result = node.execute()
                
                if result:
                    # Get the output data from the node
                    output_data = None
                    
                    # Try different ways to get output data
                    if hasattr(node, 'output_data') and node.output_data is not None:
                        output_data = node.output_data
                        print(f"TRANSFORMATION: Got output_data with shape: {output_data.shape}")
                    elif hasattr(node, 'get_output_data') and callable(node.get_output_data):
                        output_data = node.get_output_data()
                        print(f"TRANSFORMATION: Got data via get_output_data() with shape: {output_data.shape if output_data is not None else 'None'}")
                    
                    # If we still don't have output data, check if the node modified input data in place
                    if output_data is None and input_data is not None:
                        output_data = input_data
                        print(f"TRANSFORMATION: Using input data as output (in-place modification)")
                    
                    if output_data is not None:
                        # Store the output data in cache
                        self.node_outputs[node] = output_data
                        self.node_outputs[node.title] = output_data
                        print(f"TRANSFORMATION SUCCESS: {node.title} - Cached output with shape: {output_data.shape}")
                        return True
                    else:
                        print(f"TRANSFORMATION ERROR: {node.title} - No output data available after execution")
                        return False
                else:
                    print(f"TRANSFORMATION ERROR: {node.title} - execute() returned False")
                    return False
            else:
                print(f"TRANSFORMATION ERROR: {node.title} - No execute() method available")
                return False
                
        except Exception as e:
            error_msg = f"Transformation node execution failed: {str(e)}"
            print(f"{error_msg}")
            import traceback
            traceback.print_exc()
            return False
            
    def validate_flow(self):
        """Validate that the flow can be executed."""
        if not self.canvas.nodes:
            print("No nodes in flow")
            return False
        print(f"Flow validation passed - {len(self.canvas.nodes)} nodes")
        return True
        
    def calculate_execution_order(self):
        """Calculate the order in which to execute nodes based on dependencies."""
        # Use topological sort to determine execution order
        from collections import defaultdict, deque
        
        # Build dependency graph
        graph = defaultdict(list)  # node -> [dependent_nodes]
        in_degree = defaultdict(int)  # node -> number of dependencies
        
        # Initialize all nodes with zero in-degree
        for node in self.canvas.nodes:
            in_degree[node] = 0
            
        # Build the graph from connections
        for conn in self.canvas.connections:
            source_node = conn.start_port.parent_node
            target_node = conn.end_port.parent_node
            graph[source_node].append(target_node)
            in_degree[target_node] += 1
        
        # Topological sort using Kahn's algorithm
        queue = deque()
        execution_order = []
        
        # Start with nodes that have no dependencies (data input nodes)
        for node in self.canvas.nodes:
            if in_degree[node] == 0:
                queue.append(node)
                
        while queue:
            current_node = queue.popleft()
            execution_order.append(current_node)
            
            # Process all dependent nodes
            for dependent_node in graph[current_node]:
                in_degree[dependent_node] -= 1
                if in_degree[dependent_node] == 0:
                    queue.append(dependent_node)
                    
        # Check for circular dependencies
        if len(execution_order) != len(self.canvas.nodes):
            print(f"Warning: Circular dependency detected. Only {len(execution_order)} of {len(self.canvas.nodes)} nodes can be executed.")
            
        return execution_order
        
    def get_node_input_data(self, node):
        """Get the input dataframe for a node after execution."""
        # Special case: Data input nodes don't need input connections
        if hasattr(node, 'filename'):
            print(f"Data input node {node.title} - checking for pre-loaded data")
            # For data input nodes, return their own dataframe if available
            if hasattr(node, 'dataframe') and node.dataframe is not None:
                print(f"Found pre-loaded dataframe: {node.dataframe.shape}")
                return node.dataframe
            else:
                print(f"No dataframe loaded for data input node: {node.title}")
                return None
        
        # Find input connections for this node
        input_connections = []
        for conn in self.canvas.connections:
            if conn.end_port.parent_node == node:
                input_connections.append(conn)
                
        if not input_connections:
            print(f"Node {node.title} has no input connections")
            return None
            
        if len(input_connections) == 1:
            # Single input - return the output of the source node
            source_node = input_connections[0].start_port.parent_node
            
            # Check cache using node object first, then title
            if source_node in self.node_outputs:
                print(f"Found cached data for source node {source_node.title} using node object")
                return self.node_outputs[source_node]
            elif source_node.title in self.node_outputs:
                print(f"Found cached data for source node {source_node.title} using title")
                return self.node_outputs[source_node.title]
            else:
                print(f"Source node {source_node.title} has no output data")
                return None
        else:
            # Multiple inputs - use first one for now
            source_node = input_connections[0].start_port.parent_node
            
            # Check cache using node object first, then title
            if source_node in self.node_outputs:
                print(f"Found cached data for source node {source_node.title} using node object")
                return self.node_outputs[source_node]
            elif source_node.title in self.node_outputs:
                print(f"Found cached data for source node {source_node.title} using title")
                return self.node_outputs[source_node.title]
            else:
                print(f"Source node {source_node.title} has no output data")
                return None
                
    def clear_failure_tracking(self):
        """Clear all failure tracking."""
        self.failed_nodes.clear()
        self.invalid_nodes.clear()
        self.last_error = None
        
    def clear_outputs(self):
        """Clear all node outputs."""
        self.node_outputs.clear()
        
    def get_node_output_data(self, node):
        """Get the output dataframe for a node after execution."""
        # Check cache using node object first, then title for compatibility
        if node in self.node_outputs:
            print(f"Found output data for {node.title} using node object")
            return self.node_outputs[node]
        elif node.title in self.node_outputs:
            print(f"Found output data for {node.title} using title")
            return self.node_outputs[node.title]
        else:
            print(f"No output data found for {node.title}")
            return None
            
    def get_last_error(self):
        """Get the last execution error."""
        return getattr(self, 'last_error', None)
        
    def validate_expression_node_before_execution(self, node):
        """Validate ExpressionBuilderNode for duplicate column names before execution."""
        try:
            print(f"🔍 VALIDATION: Checking expression node {node.title} for duplicate columns")
            
            # Get existing columns from input data
            input_data = self.get_node_input_data(node)
            if input_data is None:
                print(f"⚠️ VALIDATION: No input data for {node.title}, allowing execution")
                return True
                
            existing_columns = set(input_data.columns)
            print(f"🔍 VALIDATION: Found {len(existing_columns)} existing columns")
            
            # Check expressions - look for multiple_expressions first, then expressions
            expressions = []
            if hasattr(node, 'multiple_expressions') and node.multiple_expressions:
                expressions = node.multiple_expressions
                print(f"🔍 VALIDATION: Using multiple_expressions with {len(expressions)} entries")
            elif hasattr(node, 'expressions') and node.expressions:
                expressions = node.expressions
                print(f"🔍 VALIDATION: Using expressions with {len(expressions)} entries")
            
            if not expressions:
                print(f"🔍 VALIDATION: No expressions found in {node.title}, allowing execution")
                return True
            
            # Validate each expression for duplicate column names
            for i, expr in enumerate(expressions):
                if isinstance(expr, dict):
                    mode = expr.get('mode', '').lower()
                    new_column = expr.get('new_column', '').strip()
                    
                    if mode == 'append' and new_column:
                        # Check if new column conflicts with existing columns (case-insensitive)
                        existing_columns_lower = {col.lower() for col in existing_columns}
                        if new_column.lower() in existing_columns_lower:
                            # Import here to avoid circular imports
                            try:
                                from PyQt6.QtWidgets import QMessageBox
                                QMessageBox.critical(None, "Flow Execution Error", 
                                    f"❌ Duplicate Column Error in {node.title}\n\n"
                                    f"Expression {i+1}: Column '{new_column}' already exists!\n\n"
                                    f"Please fix this issue before executing the workflow.\n"
                                    f"Either:\n• Choose a different column name\n• Remove the conflicting expression")
                            except ImportError:
                                print(f"❌ VALIDATION ERROR: Cannot show dialog (PyQt6 not available)")
                            
                            print(f"❌ VALIDATION FAILED: {node.title} expression {i+1} creates duplicate column '{new_column}'")
                            return False
                        
                        print(f"✅ VALIDATION: Expression {i+1} column '{new_column}' is valid")
                    
            print(f"✅ VALIDATION: All expressions in {node.title} are valid")
            return True
            
        except Exception as e:
            print(f"⚠️ VALIDATION ERROR: {e}")
            # Allow execution if validation fails to avoid blocking valid workflows
            return True
        
    def get_cache_info(self):
        """Get information about cached outputs for debugging."""
        cache_info = {
            'total_cached': len(self.node_outputs),
            'cached_keys': list(self.node_outputs.keys()),
            'node_types': [type(key).__name__ for key in self.node_outputs.keys()]
        }
        print(f"CACHE INFO: {cache_info}")
        return cache_info


# For backward compatibility
ExecutionEngine = FlowExecutionEngine
