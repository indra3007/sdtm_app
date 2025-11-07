"""
🚀 Flow Execution Engine
Handles executing data transformation flows through connected nodes
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
        self.log_callback = None  # Callback function for logging messages
        
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
            self.log("🚀 Starting flow execution...")
            
            # Clear previous failure tracking
            self.clear_failure_tracking()
            
            # 1. Validate flow
            if not self.validate_flow():
                self.log("❌ Flow validation failed")
                return False
                
            # 2. Determine execution order
            self.execution_order = self.calculate_execution_order()
            if not self.execution_order:
                self.log("❌ Could not determine execution order - possible circular dependencies")
                return False
                
            self.log(f"📋 Execution order: {[node.title for node in self.execution_order]}")
            
            # 3. Execute nodes in order
            total_nodes = len(self.execution_order)
            successful_nodes = 0
            failed_nodes = 0
            
            for i, node in enumerate(self.execution_order):
                self.log(f"⏳ Executing {i+1}/{total_nodes}: {node.title}")
                
                # Log node details before execution
                self.log_node_details(node, "STARTING")
                
                if not self.execute_node(node):
                    failed_nodes += 1
                    # Log failure details
                    self.log_node_details(node, "FAILED")
                    self.log(f"❌ Failed to execute node: {node.title}")
                    
                    # Clear downstream outputs to prevent showing stale data
                    self.clear_downstream_outputs(node)
                    
                    # CRITICAL FIX: Continue execution instead of breaking
                    # This allows upstream nodes to keep their data and downstream independent branches to continue
                    self.log(f"⏭️ Continuing execution - upstream nodes retain data")
                    continue  # Continue to next node instead of breaking
                else:
                    successful_nodes += 1
                    # Log success details
                    self.log_node_details(node, "SUCCESS")
                    self.log(f"✅ Completed: {node.title}")
            
            # Final summary
            if failed_nodes == 0:
                self.log(f"🎉 Flow execution completed successfully!")
                self.log(f"📊 Summary: {successful_nodes}/{total_nodes} nodes executed successfully")
                return True
            else:
                self.log(f"❌ Flow execution failed!")
                self.log(f"📊 Summary: {successful_nodes} successful, {failed_nodes} failed, {total_nodes - successful_nodes - failed_nodes} skipped")
                return False
            
        except Exception as e:
            error_msg = f"Fatal execution error: {str(e)}"
            self.log(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False
    
    def validate_flow(self):
        """Validate that the flow can be executed."""
        # Check if we have nodes
        if not self.canvas.nodes:
            print("❌ No nodes in flow")
            return False
            
        # Check if we have data input nodes
        data_nodes = [node for node in self.canvas.nodes if hasattr(node, 'filename')]
        if not data_nodes:
            print("❌ No data input nodes found")
            return False
            
        print(f"✅ Flow validation passed - {len(self.canvas.nodes)} nodes, {len(self.canvas.connections)} connections")
        return True
        
    def calculate_execution_order(self):
        """Calculate the order in which to execute nodes (topological sort)."""
        # Start with data input nodes (no dependencies)
        execution_order = []
        remaining_nodes = list(self.canvas.nodes)
        processed_nodes = set()
        
        # First, add all data input nodes
        for node in list(remaining_nodes):
            if hasattr(node, 'filename'):  # Data input node
                execution_order.append(node)
                remaining_nodes.remove(node)
                processed_nodes.add(node)
                
        # Then process transformation nodes based on dependencies
        max_iterations = len(remaining_nodes) + 1
        iteration = 0
        
        while remaining_nodes and iteration < max_iterations:
            iteration += 1
            nodes_added_this_iteration = []
            
            for node in list(remaining_nodes):
                # Check if all input dependencies are satisfied
                input_dependencies_met = True
                
                for connection in self.canvas.connections:
                    if connection.end_port.parent_node == node:  # This node receives input
                        source_node = connection.start_port.parent_node
                        if source_node not in processed_nodes:
                            input_dependencies_met = False
                            break
                
                if input_dependencies_met:
                    execution_order.append(node)
                    remaining_nodes.remove(node)
                    processed_nodes.add(node)
                    nodes_added_this_iteration.append(node)
                    
            # If no nodes were added this iteration, we might have a cycle
            if not nodes_added_this_iteration:
                print("⚠️ Possible circular dependency detected")
                # Add remaining nodes anyway (best effort)
                execution_order.extend(remaining_nodes)
                break
                
        return execution_order
        
    def log_node_details(self, node, status):
        """Log detailed information about a node and its execution status."""
        try:
            details = []
            details.append(f"📋 NODE DETAILS [{status}]: {node.title}")
            
            # Node type and properties
            node_type = node.__class__.__name__
            details.append(f"   Type: {node_type}")
            
            # Log specific properties based on node type
            if hasattr(node, 'filename'):  # Data input node
                details.append(f"   File: {node.filename}")
                if hasattr(node, 'dataframe') and node.dataframe is not None:
                    details.append(f"   Input Shape: {node.dataframe.shape}")
                    details.append(f"   Columns: {list(node.dataframe.columns)[:5]}{'...' if len(node.dataframe.columns) > 5 else ''}")
                    
            elif hasattr(node, 'rename_mappings'):  # Column renamer
                if node.rename_mappings:
                    details.append(f"   Rename Mappings: {dict(list(node.rename_mappings.items())[:3])}{'...' if len(node.rename_mappings) > 3 else ''}")
                else:
                    details.append(f"   Rename Mappings: None configured")
                    
            elif hasattr(node, 'expressions'):  # Expression builder
                if hasattr(node, 'multiple_expressions') and node.multiple_expressions:
                    expr_count = len(node.multiple_expressions)
                    details.append(f"   Expressions: {expr_count} configured")
                    for i, expr in enumerate(node.multiple_expressions[:2]):  # Show first 2
                        col = expr.get('column', 'Unknown')
                        func = expr.get('function', 'Unknown')
                        details.append(f"     {i+1}. {col} -> {func}")
                    if expr_count > 2:
                        details.append(f"     ... and {expr_count - 2} more")
                else:
                    details.append(f"   Expressions: None configured")
                    
            elif hasattr(node, 'column_name') and hasattr(node, 'constant_value'):  # Constant value
                details.append(f"   Column: {node.column_name}")
                details.append(f"   Value: {node.constant_value}")
                
            elif hasattr(node, 'filter_column'):  # Row filter
                details.append(f"   Filter Column: {getattr(node, 'filter_column', 'None')}")
                details.append(f"   Filter Operator: {getattr(node, 'filter_operator', 'None')}")
                details.append(f"   Filter Value: {getattr(node, 'filter_value', 'None')}")
            
            # Input/output information
            if status in ["SUCCESS", "FAILED"]:
                # Get input data info
                input_data = self.get_node_input_data(node)
                if input_data is not None:
                    details.append(f"   Input Data: {input_data.shape} - {len(input_data.columns)} columns")
                else:
                    details.append(f"   Input Data: None")
                
                # Get output data info (for successful nodes)
                if status == "SUCCESS":
                    output_data = self.node_outputs.get(node, None)
                    if output_data is not None:
                        details.append(f"   Output Data: {output_data.shape} - {len(output_data.columns)} columns")
                        
                        # Show column changes
                        if input_data is not None:
                            input_cols = set(input_data.columns)
                            output_cols = set(output_data.columns)
                            new_cols = output_cols - input_cols
                            removed_cols = input_cols - output_cols
                            
                            if new_cols:
                                details.append(f"   New Columns: {list(new_cols)[:3]}{'...' if len(new_cols) > 3 else ''}")
                            if removed_cols:
                                details.append(f"   Removed Columns: {list(removed_cols)[:3]}{'...' if len(removed_cols) > 3 else ''}")
                    else:
                        details.append(f"   Output Data: None")
                        
                elif status == "FAILED":
                    # Log error details
                    if self.last_error:
                        details.append(f"   Error: {self.last_error}")
                    details.append(f"   Output Data: Failed to generate")
            
            # Log all details
            for detail in details:
                self.log(detail)
                
        except Exception as e:
            self.log(f"⚠️ Error logging node details for {node.title}: {str(e)}")
    
    def execute_node(self, node):
        """Execute a single node and its dependencies."""
        try:
            print(f"🎯 EXECUTE NODE: Starting execution for {node.title}")
            self.last_error = None  # Clear previous error
            
            # Set node status to running
            node.set_execution_status("running", 10)
            
            # First, ensure all input dependencies are executed
            if not self.execute_node_dependencies(node):
                error_msg = f"Failed to execute dependencies for {node.title}"
                print(f"❌ {error_msg}")
                self.last_error = error_msg
                node.set_execution_status("error")
                return False
            
            # Update progress
            node.set_execution_status("running", 30)
            
            # Now execute the node itself
            success = False
            if hasattr(node, 'filename'):  # Data input node
                success = self.execute_data_input_node(node)
            elif hasattr(node, 'rename_mappings'):  # Column renamer node
                success = self.execute_column_renamer_node(node)
            elif hasattr(node, 'expression'):  # Expression builder node
                success = self.execute_expression_builder_node(node)
            elif hasattr(node, 'column_name') and hasattr(node, 'constant_value'):  # Constant value column node
                success = self.execute_constant_value_node(node)
            elif hasattr(node, 'filter_column'):  # Row filter node
                success = self.execute_row_filter_node(node)
            elif hasattr(node, 'source_column') and hasattr(node, 'mappings'):  # Conditional mapping node
                success = self.execute_conditional_mapping_node(node)
            elif hasattr(node, 'domain_codes') and hasattr(node, 'selected_domain'):  # Domain node
                success = self.execute_domain_node(node)
            elif hasattr(node, 'included_columns') and hasattr(node, 'excluded_columns'):  # Column keep/drop node
                success = self.execute_column_keep_drop_node(node)
            else:
                print(f"⚠️ Unknown node type: {node.title}")
                # For unknown nodes, just pass through input data
                input_data = self.get_node_input_data(node)
                if input_data is not None:
                    self.node_outputs[node] = input_data
                    success = True
                else:
                    error_msg = f"Unknown node type and no input data available for {node.title}"
                    self.last_error = error_msg
                    success = False
            
            # Update status based on execution result
            if success:
                node.set_execution_status("success")
                print(f"✅ Completed: {node.title}")
            else:
                node.set_execution_status("error")
                
            return success
                
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ Error executing node {node.title}: {error_msg}")
            traceback.print_exc()
            self.last_error = error_msg
            
            # Set node status to error
            node.set_execution_status("error")
            
            # Mark this node as failed
            self.failed_nodes.add(node)
            self.log(f"🚫 Marked node as failed: {node.title}")
            
            # Mark all downstream nodes as invalid
            downstream_nodes = self.find_downstream_nodes(node)
            for downstream_node in downstream_nodes:
                self.invalid_nodes.add(downstream_node)
                downstream_node.set_execution_status("error")  # Mark downstream as error too
                self.log(f"🚫 Marked downstream node as invalid: {downstream_node.title}")
            
            # Clear any stale output data for this node
            if node in self.node_outputs:
                del self.node_outputs[node]
                self.log(f"🧹 Cleared stale output data for failed node: {node.title}")
            
            # Clear downstream node outputs to prevent showing stale data
            self.clear_downstream_outputs(node)
            
            return False
    
    def get_last_error(self):
        """Get the last execution error message."""
        return self.last_error
    
    def is_node_failed(self, node):
        """Check if a node has failed execution."""
        return node in self.failed_nodes
    
    def is_node_invalid(self, node):
        """Check if a node is invalid due to upstream failures."""
        return node in self.invalid_nodes or node in self.failed_nodes
    
    def clear_failure_tracking(self):
        """Clear all failure tracking - used when starting new execution."""
        self.failed_nodes.clear()
        self.invalid_nodes.clear()
        self.last_error = None
        print("🧹 Cleared failure tracking")
        
        # Reset all node execution status
        if hasattr(self.canvas, 'nodes'):
            for node in self.canvas.nodes:
                node.reset_execution_status()
            print("🔄 Reset all node execution status")
    
    def execute_node_dependencies(self, node):
        """Execute all input dependencies for a node."""
        try:
            print(f"🔍 DEPENDENCIES: Checking dependencies for {node.title}")
            
            # Find all input connections for this node
            input_connections = [
                conn for conn in self.canvas.connections 
                if conn.end_port.parent_node == node
            ]
            
            if not input_connections:
                print(f"ℹ️ DEPENDENCIES: {node.title} has no input dependencies")
                return True
            
            # Execute each source node if not already executed
            for conn in input_connections:
                source_node = conn.start_port.parent_node
                print(f"🔍 DEPENDENCIES: Checking source node {source_node.title}")
                
                if source_node not in self.node_outputs:
                    print(f"⚡ DEPENDENCIES: Executing prerequisite {source_node.title}")
                    
                    # Check if this source node is marked as failed
                    if source_node in self.failed_nodes:
                        print(f"❌ DEPENDENCIES: Source node {source_node.title} is marked as failed - skipping")
                        return False
                    
                    # Avoid infinite recursion by checking if it's a data input node
                    if hasattr(source_node, 'filename'):
                        # This is a data input node - execute it directly
                        if not self.execute_data_input_node(source_node):
                            print(f"❌ DEPENDENCIES: Failed to execute data input {source_node.title}")
                            return False
                    else:
                        # This is a transformation node - execute with dependencies
                        if not self.execute_node(source_node):
                            print(f"❌ DEPENDENCIES: Failed to execute prerequisite {source_node.title}")
                            return False
                else:
                    print(f"✅ DEPENDENCIES: {source_node.title} already executed")
            
            print(f"✅ DEPENDENCIES: All dependencies ready for {node.title}")
            return True
            
        except Exception as e:
            print(f"❌ DEPENDENCIES ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def execute_data_input_node(self, node):
        """Execute a data input node."""
        print(f"📥 Processing data input: {node.title}")
        print(f"📥 Node has filename: {hasattr(node, 'filename')}")
        print(f"📥 Node has dataframe: {hasattr(node, 'dataframe')}")
        
        if hasattr(node, 'dataframe'):
            print(f"📥 Dataframe is None: {node.dataframe is None}")
            if node.dataframe is not None:
                print(f"📥 Dataframe shape: {node.dataframe.shape}")
        
        # Data input nodes should have their dataframe loaded
        if hasattr(node, 'dataframe') and node.dataframe is not None:
            output_df = node.dataframe.copy()
            self.node_outputs[node] = output_df
            print(f"📊 Data input ready: {len(output_df)} rows, {len(output_df.columns)} columns")
            print(f"📊 Columns: {list(output_df.columns)[:10]}...")  # Show first 10 columns
            return True
        elif hasattr(node, 'filename'):
            # Try to load the data if filename is available but dataframe is not
            print(f"📥 Attempting to load data from {getattr(node, 'filename', 'No filename')}")
            try:
                # This would require data loading logic here
                # For now, let's check if there's a way to trigger data loading
                print(f"⚠️ Data not loaded for {getattr(node, 'filename', 'unknown')} - node needs data loaded first")
                print(f"💡 Tip: Load data via File → Load Data before executing transformations")
                return False
            except Exception as e:
                print(f"❌ Failed to load data for {getattr(node, 'filename', 'unknown')}: {e}")
                return False
        else:
            print(f"❌ No dataframe or filename found in data input node")
            print(f"💡 Node attributes: {[attr for attr in dir(node) if not attr.startswith('_')]}")
            return False
    
    def execute_column_renamer_node(self, node):
        """Execute a column renamer node."""
        print(f"🏷️ Processing column renamer...")
        
        # Get input data
        input_df = self.get_node_input_data(node)
        if input_df is None:
            print(f"❌ No input data for column renamer")
            return False
            
        # Apply column renaming with validation
        output_df = input_df.copy()
        
        if hasattr(node, 'rename_mappings') and node.rename_mappings:
            # Validate rename mappings before applying
            existing_columns = set(output_df.columns)
            new_column_names = set()
            valid_rename_dict = {}
            errors = []
            
            for old_name, new_name in node.rename_mappings.items():
                if old_name not in output_df.columns:
                    errors.append(f"❌ Column '{old_name}' not found in input data")
                    continue
                    
                if not new_name.strip():
                    errors.append(f"❌ Empty new name for column '{old_name}'")
                    continue
                
                clean_new_name = new_name.strip()
                
                # Check if trying to rename to an existing column (unless it's the same column)
                if clean_new_name in existing_columns and clean_new_name != old_name:
                    errors.append(f"❌ Cannot rename '{old_name}' to '{clean_new_name}' - column already exists")
                    continue
                
                # Check for duplicate new names in this operation
                if clean_new_name in new_column_names:
                    errors.append(f"❌ Duplicate new column name '{clean_new_name}' in rename operation")
                    continue
                
                valid_rename_dict[old_name] = clean_new_name
                new_column_names.add(clean_new_name)
            
            # Show errors if any validation failed
            if errors:
                error_msg = "\n".join(errors)
                print(f"❌ Column rename validation failed:\n{error_msg}")
                raise ValueError(f"Column rename validation failed:\n{error_msg}")
            
            # Apply valid renames
            if valid_rename_dict:
                output_df = output_df.rename(columns=valid_rename_dict)
                print(f"🏷️ Successfully renamed columns: {valid_rename_dict}")
            else:
                print(f"ℹ️ No valid column mappings found")
        else:
            print(f"ℹ️ No rename mappings configured")
            
        self.node_outputs[node] = output_df
        print(f"✅ Column renamer output: {len(output_df)} rows, {len(output_df.columns)} columns")
        return True
    
    def execute_expression_builder_node(self, node):
        """Execute an expression builder node with SAS functions."""
        print(f"📝 Processing expression builder...")
        
        # Get input data
        input_df = self.get_node_input_data(node)
        if input_df is None:
            print(f"❌ No input data for expression builder")
            return False
            
        try:
            # Use the node's process_data method which handles SAS functions
            output_df = node.process_data(input_df)
            
            if output_df is not None:
                self.node_outputs[node] = output_df
                print(f"✅ Expression builder output: {len(output_df)} rows, {len(output_df.columns)} columns")
                
                # Log the transformation details
                if hasattr(node, 'function_type') and hasattr(node, 'target_column'):
                    operation = "replaced" if node.operation_mode == "replace" else "created"
                    target = node.target_column if node.operation_mode == "replace" else node.new_column_name
                    print(f"📝 Applied {node.function_type} function to '{node.target_column}', {operation} column '{target}'")
                
                return True
            else:
                print(f"❌ Expression builder returned no data")
                return False
                
        except Exception as e:
            print(f"❌ Error in expression builder: {str(e)}")
            return False
    
    def execute_constant_value_node(self, node):
        """Execute a constant value column node."""
        print(f"🔢 Processing constant value column...")
        
        # Get input data
        input_df = self.get_node_input_data(node)
        if input_df is None:
            print(f"❌ No input data for constant value column")
            return False
            
        # Use the node's process_data method
        try:
            output_df = node.process_data(input_df)
            if output_df is None:
                print(f"❌ Constant value column processing failed")
                return False
                
            self.node_outputs[node] = output_df
            print(f"✅ Constant value column output: {len(output_df)} rows, {len(output_df.columns)} columns")
            return True
            
        except Exception as e:
            print(f"❌ Error in constant value column processing: {str(e)}")
            return False
    
    def execute_row_filter_node(self, node):
        """Execute a row filter node."""
        print(f"🔍 Processing row filter...")
        
        # Get input data
        input_df = self.get_node_input_data(node)
        if input_df is None:
            print(f"❌ No input data for row filter")
            return False
            
        # Check if we have either primary filter or combined conditions
        has_primary_filter = bool(node.filter_column)
        has_combined_conditions = bool(getattr(node, 'conditions', []))
        
        if not has_primary_filter and not has_combined_conditions:
            print(f"❌ No filter conditions configured")
            return False
            
        # Validate primary filter column if specified
        if has_primary_filter and node.filter_column not in input_df.columns:
            print(f"❌ Column '{node.filter_column}' not found in data")
            return False
            
        print(f"🔍 Filtering column: {node.filter_column}")
        print(f"🔍 Filter operator: {node.filter_operator}")
        print(f"🔍 Filter value: '{node.filter_value}'")
        print(f"🔍 Case sensitive: {node.case_sensitive}")
        print(f"🔍 Output mode: {node.output_mode}")
        print(f"🔍 Additional conditions: {len(getattr(node, 'conditions', []))}")
        print(f"🔍 Logic operator: {getattr(node, 'logic_operator', 'AND')}")
        print(f"🔍 Input rows: {len(input_df)}")
        
        # Apply filter based on operator
        output_df = self.apply_row_filter(input_df, node)
        
        if output_df is not None:
            self.node_outputs[node] = output_df
            print(f"✅ Row filter output: {len(output_df)} rows, {len(output_df.columns)} columns")
            print(f"📊 Filtered out: {len(input_df) - len(output_df)} rows")
            return True
        else:
            print(f"❌ Row filter failed")
            return False
    
    def apply_row_filter(self, df, node):
        """Apply the actual row filtering logic with support for multiple conditions."""
        try:
            # Check if we have a primary filter condition
            has_primary_filter = bool(node.filter_column)
            has_combined_conditions = bool(getattr(node, 'conditions', []))
            
            primary_mask = None
            if has_primary_filter:
                # Apply the primary filter condition
                primary_mask = self.apply_single_condition(df, node.filter_column, node.filter_operator, node.filter_value, node.case_sensitive)
                if primary_mask is None:
                    return None
            
            # Apply additional conditions if they exist
            if has_combined_conditions:
                print(f"🔍 Applying {len(node.conditions)} combined conditions with {getattr(node, 'logic_operator', 'AND')} logic")
                
                combined_mask = None
                for i, condition in enumerate(node.conditions):
                    condition_mask = self.apply_single_condition(
                        df, 
                        condition['column'], 
                        condition['operator'], 
                        condition['value'], 
                        condition['case_sensitive']
                    )
                    
                    if condition_mask is not None:
                        if combined_mask is None:
                            combined_mask = condition_mask
                        else:
                            logic_op = getattr(node, 'logic_operator', 'AND')
                            if logic_op == 'AND':
                                combined_mask = combined_mask & condition_mask
                            else:  # OR
                                combined_mask = combined_mask | condition_mask
                        print(f"🔍 Applied condition {i+1} with {getattr(node, 'logic_operator', 'AND')} logic")
                
                # Combine primary and combined conditions
                if primary_mask is not None and combined_mask is not None:
                    # If we have both primary and combined conditions, combine them with AND
                    final_mask = primary_mask & combined_mask
                elif combined_mask is not None:
                    # If we only have combined conditions, use those
                    final_mask = combined_mask
                else:
                    # If we only have primary condition, use that
                    final_mask = primary_mask
            else:
                # Only primary filter
                final_mask = primary_mask
            
            if final_mask is None:
                print("❌ No valid conditions to apply")
                return None
            
            # Apply output mode
            if getattr(node, 'output_mode', 'matching') == "non-matching":
                # Invert the mask for non-matching rows
                final_mask = ~final_mask
                print(f"📊 Inverted mask for non-matching rows")
            
            filtered_df = df[final_mask].copy()
            
            matching_count = final_mask.sum() if getattr(node, 'output_mode', 'matching') == "matching" else (~final_mask).sum()
            print(f"📊 Filter result: {len(filtered_df)} {getattr(node, 'output_mode', 'matching')} rows out of {len(df)} total rows")
            
            return filtered_df
            
        except Exception as e:
            print(f"❌ Error applying filter: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def apply_single_condition(self, df, column, operator, value, case_sensitive):
        """Apply a single filter condition and return the mask."""
        try:
            if not column or column not in df.columns:
                print(f"❌ Column '{column}' not found in data")
                return None
            
            # Get the column data
            col_data = df[column]
            
            # Apply filtering based on operator
            if operator == "is missing":
                mask = col_data.isna()
            elif operator == "is not missing":
                mask = col_data.notna()
            elif operator == "equals":
                if case_sensitive:
                    mask = col_data == value
                else:
                    mask = col_data.astype(str).str.lower() == str(value).lower()
            elif operator == "not equals":
                if case_sensitive:
                    mask = col_data != value
                else:
                    mask = col_data.astype(str).str.lower() != str(value).lower()
            elif operator == "contains":
                if case_sensitive:
                    mask = col_data.astype(str).str.contains(value, na=False)
                else:
                    mask = col_data.astype(str).str.lower().str.contains(str(value).lower(), na=False)
            elif operator == "starts with":
                if case_sensitive:
                    mask = col_data.astype(str).str.startswith(value, na=False)
                else:
                    mask = col_data.astype(str).str.lower().str.startswith(str(value).lower(), na=False)
            elif operator == "ends with":
                if case_sensitive:
                    mask = col_data.astype(str).str.endswith(value, na=False)
                else:
                    mask = col_data.astype(str).str.lower().str.endswith(str(value).lower(), na=False)
            elif operator == "greater than":
                mask = pd.to_numeric(col_data, errors='coerce') > pd.to_numeric(value, errors='coerce')
            elif operator == "less than":
                mask = pd.to_numeric(col_data, errors='coerce') < pd.to_numeric(value, errors='coerce')
            elif operator == "greater or equal":
                mask = pd.to_numeric(col_data, errors='coerce') >= pd.to_numeric(value, errors='coerce')
            elif operator == "less or equal":
                mask = pd.to_numeric(col_data, errors='coerce') <= pd.to_numeric(value, errors='coerce')
            else:
                print(f"❌ Unknown operator: {operator}")
                return None
                
            return mask
            
        except Exception as e:
            print(f"❌ Error applying single condition: {str(e)}")
            return None
    
    def execute_conditional_mapping_node(self, node):
        """Execute a conditional mapping node with support for multiple configurations."""
        print(f"🗂️ Processing conditional mapping...")
        
        # Get input data
        input_df = self.get_node_input_data(node)
        if input_df is None:
            print(f"❌ No input data for conditional mapping")
            return False
        
        # Check for multiple configurations or legacy configuration
        configs_to_validate = []
        
        if hasattr(node, 'mapping_configs') and node.mapping_configs:
            configs_to_validate = node.mapping_configs
        else:
            # Fallback to legacy properties
            legacy_config = {
                'source_column': getattr(node, 'source_column', ''),
                'target_column': getattr(node, 'target_column', ''),
                'mappings': getattr(node, 'mappings', []),
                'operation_mode': getattr(node, 'operation_mode', 'add_column')
            }
            configs_to_validate = [legacy_config]
        
        # Validate at least one valid configuration exists
        valid_configs = 0
        for config in configs_to_validate:
            source_column = config.get('source_column', '')
            target_column = config.get('target_column', '')
            mappings = config.get('mappings', [])
            operation_mode = config.get('operation_mode', 'add_column')
            
            # Validation depends on operation mode
            if operation_mode == "replace_column":
                # For replace mode: only source_column and mappings required
                config_valid = source_column and mappings
            else:
                # For add_column mode: source_column, target_column, and mappings required
                config_valid = source_column and target_column and mappings
            
            if config_valid:
                # Validate source column exists
                if source_column in input_df.columns:
                    valid_configs += 1
                    print(f"✅ Valid config: {operation_mode} mode - '{source_column}' → {'replace in-place' if operation_mode == 'replace_column' else target_column}")
                else:
                    print(f"⚠️ Source column '{source_column}' not found in data")
            else:
                print(f"⚠️ Invalid config: missing required fields for {operation_mode} mode")
        
        if valid_configs == 0:
            print(f"❌ No valid configurations found")
            return False
        
        print(f"🗂️ Found {valid_configs} valid configuration(s)")
        print(f"🗂️ Input rows: {len(input_df)}")
        
        # Apply conditional mapping
        output_df = self.apply_conditional_mapping(input_df, node)
        
        if output_df is not None:
            self.node_outputs[node] = output_df
            print(f"✅ Conditional mapping output: {len(output_df)} rows, {len(output_df.columns)} columns")
            
            # Show results for each configuration
            if hasattr(node, 'mapping_configs') and node.mapping_configs:
                for config in node.mapping_configs:
                    target_column = config.get('target_column', '')
                    if target_column and target_column in output_df.columns:
                        unique_values = output_df[target_column].value_counts()
                        print(f"📊 '{target_column}' values: {dict(unique_values)}")
            
            return True
        else:
            print(f"❌ Conditional mapping failed")
            return False
    
    def apply_conditional_mapping(self, df, node):
        """Apply the conditional mapping transformation with support for multiple configurations."""
        try:
            # Make a copy of the input dataframe
            output_df = df.copy()
            
            # Check if we have multiple configurations or legacy single configuration
            configs_to_process = []
            
            if hasattr(node, 'mapping_configs') and node.mapping_configs:
                # Use new multiple configuration structure
                configs_to_process = node.mapping_configs
                print(f"🗂️ Processing {len(configs_to_process)} mapping configurations")
            else:
                # Fallback to legacy single configuration
                legacy_config = {
                    'source_column': getattr(node, 'source_column', ''),
                    'target_column': getattr(node, 'target_column', ''),
                    'mappings': getattr(node, 'mappings', []),
                    'default_value': getattr(node, 'default_value', ''),
                    'operation_mode': getattr(node, 'operation_mode', 'add_column')
                }
                configs_to_process = [legacy_config]
                print(f"🗂️ Processing legacy single configuration")
            
            total_transformations = 0
            
            # Process each configuration
            for config_index, config in enumerate(configs_to_process):
                source_column = config.get('source_column', '')
                target_column = config.get('target_column', '')
                mappings = config.get('mappings', [])
                default_value = config.get('default_value', '')
                operation_mode = config.get('operation_mode', 'add_column')
                
                # Skip empty configurations - adjust validation based on operation mode
                if not source_column or not mappings:
                    print(f"⏭️ Skipping configuration {config_index + 1}: missing source column or mappings")
                    continue
                
                # For add_column mode, target column is required; for replace_column mode, it's not
                if operation_mode == "add_column" and not target_column:
                    print(f"⏭️ Skipping configuration {config_index + 1}: target column required for add_column mode")
                    continue
                
                # Validate source column exists
                if source_column not in output_df.columns:
                    print(f"❌ Configuration {config_index + 1}: Source column '{source_column}' not found")
                    continue
                
                print(f"🔄 Processing configuration {config_index + 1}:")
                if operation_mode == "replace_column":
                    print(f"   Source: {source_column} → Replace column values")
                else:
                    print(f"   Source: {source_column} → Target: {target_column}")
                print(f"   Mappings: {len(mappings)}, Default: '{default_value}'")
                print(f"   Mode: {operation_mode}")
                
                # Get source column data
                source_data = output_df[source_column]
                
                # Initialize target column with default value
                if default_value:
                    target_data = pd.Series([default_value] * len(output_df), index=output_df.index)
                else:
                    target_data = pd.Series([None] * len(output_df), index=output_df.index)
                
                # Apply mappings for this configuration
                mappings_applied = 0
                for mapping in mappings:
                    condition = mapping.get('condition', '')
                    result = mapping.get('result', '')
                    
                    if condition and result:
                        # Create mask for exact matches
                        mask = source_data.astype(str) == str(condition)
                        
                        # Apply the mapping
                        matched_count = mask.sum()
                        if matched_count > 0:
                            target_data[mask] = result
                            mappings_applied += matched_count
                            print(f"   🎯 '{condition}' → '{result}': {matched_count} rows")
                
                print(f"   📊 Applied {mappings_applied} mappings out of {len(output_df)} rows")
                
                # Handle operation mode for this configuration
                if operation_mode == "replace_column":
                    # Replace the source column
                    output_df[source_column] = target_data
                    print(f"   🔄 Replaced column '{source_column}' with mapped values")
                else:  # add_column (default)
                    # Add as new column
                    output_df[target_column] = target_data
                    print(f"   ➕ Added new column '{target_column}' with mapped values")
                
                total_transformations += 1
            
            print(f"✅ Successfully applied {total_transformations} conditional mapping configurations")
            return output_df
            
        except Exception as e:
            print(f"❌ Error applying conditional mapping: {str(e)}")
            return None
    
    def execute_domain_node(self, node):
        """Execute a domain node to add DOMAIN column."""
        try:
            print(f"🏷️ EXECUTE ENGINE: Processing domain node {node.title}")
            node.set_execution_status("running", 10)
            
            # Get input data
            input_data = self.get_node_input_data(node)
            if input_data is None or input_data.empty:
                print(f"❌ DOMAIN: No input data available")
                node.set_execution_status("error", 0)
                return False
            
            node.set_execution_status("running", 30)
            
            # Check if domain is selected - be more thorough
            selected_domain = getattr(node, 'selected_domain', '')
            print(f"🏷️ EXECUTE ENGINE: Node selected_domain = '{selected_domain}'")
            
            if not selected_domain:
                print(f"❌ DOMAIN: No domain selected (Execute All requires domain selection first)")
                print(f"💡 DOMAIN: Please select a domain from the dropdown in the Domain node's property panel")
                node.set_execution_status("error", 0)
                return False
            
            node.set_execution_status("running", 50)
            
            # Create output dataframe with DOMAIN column
            output_df = input_data.copy()
            output_df['DOMAIN'] = selected_domain
            
            node.set_execution_status("running", 80)
            
            # Store output data in both places for compatibility
            self.node_outputs[node] = output_df  # Use node object as key
            node.output_data = output_df  # Also store on node
            
            print(f"🏷️ DOMAIN: Added DOMAIN column with value '{selected_domain}' to {len(output_df)} rows")
            
            node.set_execution_status("success", 0)
            return True
            
        except Exception as e:
            print(f"❌ DOMAIN ERROR: {str(e)}")
            node.set_execution_status("error", 0)
            return False
    
    def get_node_input_data(self, node):
        """Get the input dataframe for a node."""
        print(f"🔍 INPUT DATA: Getting input data for {node.title}")
        
        # Find connections that feed into this node
        input_connections = [
            conn for conn in self.canvas.connections 
            if conn.end_port.parent_node == node
        ]
        
        print(f"🔍 INPUT DATA: Found {len(input_connections)} input connections")
        
        if not input_connections:
            print(f"ℹ️ Node {node.title} has no input connections")
            return None
            
        if len(input_connections) == 1:
            # Single input - return the output of the source node
            source_node = input_connections[0].start_port.parent_node
            print(f"🔍 INPUT DATA: Source node: {source_node.title}")
            print(f"🔍 INPUT DATA: Source node in outputs: {source_node in self.node_outputs}")
            
            if source_node in self.node_outputs:
                output_data = self.node_outputs[source_node]
                print(f"🔍 INPUT DATA: Found output data shape: {output_data.shape if output_data is not None else 'None'}")
                return output_data
            else:
                print(f"❌ Source node {source_node.title} has no output data")
                
                # Check if the source node has a dataframe directly
                if hasattr(source_node, 'dataframe') and source_node.dataframe is not None:
                    print(f"🔍 INPUT DATA: Source node has direct dataframe: {source_node.dataframe.shape}")
                    # Store it in outputs for future use
                    self.node_outputs[source_node] = source_node.dataframe.copy()
                    return source_node.dataframe.copy()
                else:
                    print(f"🔍 INPUT DATA: Source node has no direct dataframe either")
                
                return None
        else:
            # Multiple inputs - for now, just use the first one
            # TODO: Implement proper multi-input handling (joins, unions, etc.)
            print(f"⚠️ Node {node.title} has multiple inputs - using first one")
            source_node = input_connections[0].start_port.parent_node
            if source_node in self.node_outputs:
                return self.node_outputs[source_node]
            else:
                print(f"❌ Source node {source_node.title} has no output data")
                return None
    
    def get_node_output_data(self, node):
        """Get the output dataframe for a node after execution."""
        # CRITICAL FIX: Check for cached data FIRST - if node has successful output, return it regardless of invalid status
        result = self.node_outputs.get(node, None)
        if result is not None:
            shape_info = result.shape if hasattr(result, 'shape') else 'unknown'
            print(f"🔍 CACHE ACCESS: Found cached data for {node.title}: {shape_info}")
            return result
        
        # Only check if node is failed/invalid if there's no cached data
        if self.is_node_invalid(node):
            print(f"🚫 CACHE ACCESS: Node {node.title} is failed/invalid and has no cached data - returning None")
            return None
            
        print(f"🔍 CACHE ACCESS: No cached data for {node.title}")
        return None
    
    def clear_outputs(self):
        """Clear all node outputs."""
        self.node_outputs.clear()
        self.execution_order.clear()
        print("🧹 Execution engine cleared")
        
    def clear_downstream_outputs(self, failed_node):
        """Clear cached outputs for all nodes downstream from the failed node."""
        try:
            print(f"🧹 Clearing downstream outputs from failed node: {failed_node.title}")
            
            # DEBUG: Show what's in cache before clearing
            print(f"🔍 CACHE DEBUG: Before clearing - {len(self.node_outputs)} nodes in cache:")
            for cached_node in self.node_outputs.keys():
                data_shape = self.node_outputs[cached_node].shape if hasattr(self.node_outputs[cached_node], 'shape') else 'unknown'
                print(f"   • {cached_node.title}: {data_shape}")
            
            # Clear the failed node itself
            if failed_node in self.node_outputs:
                del self.node_outputs[failed_node]
                print(f"🧹 Cleared failed node: {failed_node.title}")
            
            # Get all downstream nodes
            downstream_nodes = self.find_downstream_nodes(failed_node)
            
            for node in downstream_nodes:
                if node in self.node_outputs:
                    del self.node_outputs[node]
                    print(f"🧹 Cleared stale output for downstream node: {node.title}")
            
            print(f"✅ Selective clear completed: cleared {len(downstream_nodes) + 1} nodes (failed + downstream)")
            print(f"💡 Upstream nodes retain their data for viewing")
            
            # DEBUG: Show what's in cache after clearing
            print(f"🔍 CACHE DEBUG: After clearing - {len(self.node_outputs)} nodes remaining:")
            for cached_node in self.node_outputs.keys():
                data_shape = self.node_outputs[cached_node].shape if hasattr(self.node_outputs[cached_node], 'shape') else 'unknown'
                print(f"   • {cached_node.title}: {data_shape}")
                    
        except Exception as e:
            print(f"⚠️ Error clearing downstream outputs: {e}")
            import traceback
            traceback.print_exc()
    
    def execute_column_keep_drop_node(self, node):
        """Execute column keep/drop node - filter columns based on includes/excludes."""
        try:
            print(f"📋 EXECUTE COLUMN KEEP/DROP: {node.title}")
            
            # Get input data
            input_data = self.get_node_input_data(node)
            if input_data is None or input_data.empty:
                self.log(f"❌ No input data for column keep/drop node: {node.title}")
                return False
            
            print(f"📋 Input data shape: {input_data.shape}")
            print(f"📋 Input columns: {list(input_data.columns)}")
            print(f"📋 Included columns: {node.included_columns}")
            print(f"📋 Excluded columns: {node.excluded_columns}")
            
            # Validate that included columns exist in input data
            input_columns = list(input_data.columns)
            valid_included = [col for col in node.included_columns if col in input_columns]
            invalid_included = [col for col in node.included_columns if col not in input_columns]
            
            if invalid_included:
                print(f"⚠️ Warning: Some included columns not found in input data: {invalid_included}")
            
            if not valid_included:
                self.log(f"❌ No valid columns to keep in node: {node.title}")
                return False
            
            # Filter the dataframe to keep only included columns
            filtered_data = input_data[valid_included].copy()
            
            print(f"📋 Filtered data shape: {filtered_data.shape}")
            print(f"📋 Kept columns: {list(filtered_data.columns)}")
            
            # Store the result
            self.node_outputs[node] = filtered_data
            
            # Log the transformation
            total_cols = len(input_columns)
            kept_cols = len(filtered_data.columns)
            dropped_cols = total_cols - kept_cols
            
            self.log(f"✅ Column Keep/Drop completed: {kept_cols} columns kept, {dropped_cols} columns dropped")
            print(f"✅ COLUMN KEEP/DROP SUCCESS: {node.title}")
            
            return True
            
        except Exception as e:
            error_msg = f"Column Keep/Drop execution failed: {str(e)}"
            self.log(f"❌ {error_msg}")
            print(f"❌ COLUMN KEEP/DROP ERROR: {error_msg}")
            traceback.print_exc()
            return False
    
    def find_downstream_nodes(self, source_node):
        """Find all nodes that are downstream from the given node."""
        downstream = set()
        to_check = [source_node]
        
        while to_check:
            current = to_check.pop()
            # Find connections where current node is the source
            for conn in self.canvas.connections:
                if conn.start_port.parent_node == current:
                    target = conn.end_port.parent_node
                    if target not in downstream:
                        downstream.add(target)
                        to_check.append(target)
        
        return list(downstream)#   F o r   b a c k w a r d   c o m p a t i b i l i t y  
 E x e c u t i o n E n g i n e   =   F l o w E x e c u t i o n E n g i n e  
 