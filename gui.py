import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import threading
import time
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from collections import deque

# Add the current directory to Python path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import our modules
try:
    from config import Config
    from process_collector import ProcessCollector
    from task_categorizer import TaskCategorizer
    from process_analyzer import ProcessAnalyzer
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all files are in the same directory:")
    print("- config.py")
    print("- process_collector.py") 
    print("- task_categorizer.py")
    print("- process_analyzer.py")
    raise

class SmartTaskManagerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Smart Task Manager - Avengers")
        self.root.geometry("1400x900")
        
        # Initialize components
        self.config = Config()
        self.process_collector = ProcessCollector()
        self.categorizer = TaskCategorizer(self.config)
        self.analyzer = ProcessAnalyzer(self.config)
        
        # Data for charts
        self.cpu_history = deque([0] * 60, maxlen=60)  # Last 60 seconds
        self.memory_history = deque([0] * 60, maxlen=60)
        self.process_count_history = deque([0] * 60, maxlen=60)
        self.category_counts = {'system': 0, 'user': 0, 'background': 0, 'suspicious': 0, 'zombie': 0, 'high_usage': 0, 'unknown': 0}
        
        self.setup_ui()
        self.update_thread = None
        self.running = False
        self.animation = None
        
    def setup_ui(self):
        """Setup the user interface with charts"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Process Management
        self.process_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.process_tab, text="Process Management")
        
        # Tab 2: Performance Charts
        self.charts_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.charts_tab, text="Performance Charts")
        
        # Tab 3: System Overview
        self.overview_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_tab, text="System Overview")
        
        self.setup_process_tab()
        self.setup_charts_tab()
        self.setup_overview_tab()
        
    def setup_process_tab(self):
        """Setup the process management tab"""
        # Header
        header_frame = tk.Frame(self.process_tab, bg='lightblue')
        header_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(header_frame, text="Smart Task Manager - Avengers", 
                font=("Arial", 16, "bold"), bg='lightblue').pack(pady=10)
        
        # System stats
        self.setup_stats_display(self.process_tab)
        
        # Process list
        self.setup_process_list(self.process_tab)
        
        # Controls
        self.setup_controls(self.process_tab)
        
    def setup_stats_display(self, parent):
        """Setup system statistics display"""
        stats_frame = tk.Frame(parent, bg='white')
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        # CPU Usage
        self.cpu_label = tk.Label(stats_frame, text="CPU: 0%", bg='white', font=("Arial", 10))
        self.cpu_label.grid(row=0, column=0, padx=10, pady=5)
        
        # Memory Usage
        self.memory_label = tk.Label(stats_frame, text="Memory: 0%", bg='white', font=("Arial", 10))
        self.memory_label.grid(row=0, column=1, padx=10, pady=5)
        
        # Battery
        self.battery_label = tk.Label(stats_frame, text="Battery: N/A", bg='white', font=("Arial", 10))
        self.battery_label.grid(row=0, column=2, padx=10, pady=5)
        
        # Process Count
        self.process_count_label = tk.Label(stats_frame, text="Processes: 0", bg='white', font=("Arial", 10))
        self.process_count_label.grid(row=0, column=3, padx=10, pady=5)
        
        # High Usage Processes
        self.high_usage_label = tk.Label(stats_frame, text="High Usage: 0", bg='white', font=("Arial", 10))
        self.high_usage_label.grid(row=0, column=4, padx=10, pady=5)
        
    def setup_process_list(self, parent):
        """Setup the process list display"""
        process_frame = tk.Frame(parent)
        process_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview for processes
        columns = ('PID', 'Name', 'CPU%', 'Memory%', 'Status', 'User', 'Categories', 'Recommendation')
        self.tree = ttk.Treeview(process_frame, columns=columns, show='headings', height=20)
        
        # Define headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(process_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind double-click event
        self.tree.bind('<Double-1>', self.on_process_select)
        
    def setup_controls(self, parent):
        """Setup control buttons"""
        control_frame = tk.Frame(parent, bg='white')
        control_frame.pack(fill="x", padx=10, pady=5)
        
        control_grid = tk.Frame(control_frame, bg='white')
        control_grid.pack(pady=10)
        
        # Control buttons
        tk.Button(control_grid, text="Refresh", command=self.refresh_processes, width=12).grid(row=0, column=0, padx=5)
        tk.Button(control_grid, text="Terminate Selected", command=self.terminate_selected, width=15).grid(row=0, column=1, padx=5)
        tk.Button(control_grid, text="Auto Clean", command=self.auto_clean, width=12).grid(row=0, column=2, padx=5)
        tk.Button(control_grid, text="Settings", command=self.open_settings, width=12).grid(row=0, column=3, padx=5)
        
        # Start/Stop monitoring
        self.monitor_btn = tk.Button(control_grid, text="Start Monitoring", 
                                   command=self.toggle_monitoring, width=15)
        self.monitor_btn.grid(row=0, column=4, padx=5)
        
    def setup_charts_tab(self):
        """Setup the performance charts tab"""
        # Create frames for charts
        charts_container = tk.Frame(self.charts_tab)
        charts_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Row 1: CPU and Memory charts
        row1_frame = tk.Frame(charts_container)
        row1_frame.pack(fill="both", expand=True)
        
        # CPU Usage Chart
        cpu_frame = tk.LabelFrame(row1_frame, text="CPU Usage Over Time", font=("Arial", 10, "bold"))
        cpu_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.cpu_fig = Figure(figsize=(6, 3), dpi=100)
        self.cpu_ax = self.cpu_fig.add_subplot(111)
        self.cpu_line, = self.cpu_ax.plot([], [], 'r-', linewidth=2)
        self.cpu_ax.set_ylabel('CPU Usage (%)')
        self.cpu_ax.set_ylim(0, 100)
        self.cpu_ax.set_xlim(0, 60)
        self.cpu_ax.grid(True, alpha=0.3)
        self.cpu_canvas = FigureCanvasTkAgg(self.cpu_fig, cpu_frame)
        self.cpu_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Memory Usage Chart
        memory_frame = tk.LabelFrame(row1_frame, text="Memory Usage Over Time", font=("Arial", 10, "bold"))
        memory_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.memory_fig = Figure(figsize=(6, 3), dpi=100)
        self.memory_ax = self.memory_fig.add_subplot(111)
        self.memory_line, = self.memory_ax.plot([], [], 'b-', linewidth=2)
        self.memory_ax.set_ylabel('Memory Usage (%)')
        self.memory_ax.set_ylim(0, 100)
        self.memory_ax.set_xlim(0, 60)
        self.memory_ax.grid(True, alpha=0.3)
        self.memory_canvas = FigureCanvasTkAgg(self.memory_fig, memory_frame)
        self.memory_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Row 2: Process count and category charts
        row2_frame = tk.Frame(charts_container)
        row2_frame.pack(fill="both", expand=True)
        
        # Process Count Chart
        process_frame = tk.LabelFrame(row2_frame, text="Process Count Over Time", font=("Arial", 10, "bold"))
        process_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.process_fig = Figure(figsize=(6, 3), dpi=100)
        self.process_ax = self.process_fig.add_subplot(111)
        self.process_line, = self.process_ax.plot([], [], 'g-', linewidth=2)
        self.process_ax.set_ylabel('Process Count')
        self.process_ax.set_ylim(0, 500)  # Adjust based on your system
        self.process_ax.set_xlim(0, 60)
        self.process_ax.grid(True, alpha=0.3)
        self.process_canvas = FigureCanvasTkAgg(self.process_fig, process_frame)
        self.process_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Process Categories Pie Chart
        pie_frame = tk.LabelFrame(row2_frame, text="Process Categories", font=("Arial", 10, "bold"))
        pie_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.pie_fig = Figure(figsize=(6, 3), dpi=100)
        self.pie_ax = self.pie_fig.add_subplot(111)
        self.pie_canvas = FigureCanvasTkAgg(self.pie_fig, pie_frame)
        self.pie_canvas.get_tk_widget().pack(fill="both", expand=True)
        
    def setup_overview_tab(self):
        """Setup system overview tab"""
        overview_frame = tk.Frame(self.overview_tab)
        overview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # System information
        info_frame = tk.LabelFrame(overview_frame, text="System Information", font=("Arial", 12, "bold"))
        info_frame.pack(fill="x", padx=5, pady=5)
        
        # System stats labels
        self.os_label = tk.Label(info_frame, text="OS: ", font=("Arial", 10), anchor="w")
        self.os_label.pack(fill="x", padx=10, pady=2)
        
        self.cpu_info_label = tk.Label(info_frame, text="CPU Cores: ", font=("Arial", 10), anchor="w")
        self.cpu_info_label.pack(fill="x", padx=10, pady=2)
        
        self.memory_info_label = tk.Label(info_frame, text="Total Memory: ", font=("Arial", 10), anchor="w")
        self.memory_info_label.pack(fill="x", padx=10, pady=2)
        
        self.disk_info_label = tk.Label(info_frame, text="Disk Usage: ", font=("Arial", 10), anchor="w")
        self.disk_info_label.pack(fill="x", padx=10, pady=2)
        
        # Top processes frame
        top_processes_frame = tk.LabelFrame(overview_frame, text="Top CPU Processes", font=("Arial", 12, "bold"))
        top_processes_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        columns = ('Name', 'CPU%', 'Memory%', 'PID')
        self.top_tree = ttk.Treeview(top_processes_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.top_tree.heading(col, text=col)
            self.top_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(top_processes_frame, orient="vertical", command=self.top_tree.yview)
        self.top_tree.configure(yscrollcommand=scrollbar.set)
        
        self.top_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def update_charts(self, frame):
        """Update all charts with current data"""
        try:
            # Update line charts
            x_data = list(range(len(self.cpu_history)))
            
            # CPU Chart
            self.cpu_line.set_data(x_data, list(self.cpu_history))
            self.cpu_ax.relim()
            self.cpu_ax.autoscale_view()
            self.cpu_canvas.draw()
            
            # Memory Chart
            self.memory_line.set_data(x_data, list(self.memory_history))
            self.memory_ax.relim()
            self.memory_ax.autoscale_view()
            self.memory_canvas.draw()
            
            # Process Count Chart
            self.process_line.set_data(x_data, list(self.process_count_history))
            self.process_ax.relim()
            self.process_ax.autoscale_view()
            self.process_canvas.draw()
            
            # Update Pie Chart
            self.pie_ax.clear()
            if any(self.category_counts.values()):
                labels = []
                sizes = []
                colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0', '#ffb3e6']
                
                for category, count in self.category_counts.items():
                    if count > 0:
                        labels.append(category)
                        sizes.append(count)
                
                if sizes:
                    self.pie_ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors[:len(sizes)])
                    self.pie_ax.axis('equal')
            
            self.pie_canvas.draw()
            
        except Exception as e:
            print(f"Chart update error: {e}")
        
    def refresh_processes(self):
        """Refresh the process list and update charts"""
        try:
            processes = self.process_collector.get_all_processes()
            system_stats = self.process_collector.get_system_stats()
            
            # Update system stats
            self.update_system_stats(system_stats)
            
            # Update chart data
            self.cpu_history.append(system_stats['cpu_percent'])
            self.memory_history.append(system_stats['memory_percent'])
            self.process_count_history.append(len(processes))
            
            # Update category counts
            self.update_category_counts(processes)
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Add processes to treeview
            high_usage_count = 0
            for proc in processes:
                try:
                    categories = self.categorizer.categorize_process(proc)
                    analysis = self.analyzer.analyze_process_health({**proc, 'categories': categories})
                    
                    # Count high usage processes
                    if 'high_usage' in categories:
                        high_usage_count += 1
                    
                    # Color coding based on categories
                    tags = ()
                    if 'suspicious' in categories:
                        tags = ('suspicious',)
                    elif 'high_usage' in categories:
                        tags = ('high_usage',)
                    elif 'zombie' in categories:
                        tags = ('zombie',)
                    
                    self.tree.insert('', 'end', values=(
                        proc['pid'],
                        proc['name'],
                        f"{proc.get('cpu_percent', 0):.1f}",
                        f"{proc.get('memory_percent', 0):.2f}",
                        proc.get('status', 'unknown'),
                        str(proc.get('username', 'unknown'))[:15],
                        ', '.join(categories),
                        analysis['recommendation']
                    ), tags=tags)
                except Exception as e:
                    print(f"Error processing PID {proc.get('pid', 'unknown')}: {e}")
                    continue
            
            # Update top processes
            self.update_top_processes(processes)
            
            # Configure tags for coloring
            self.tree.tag_configure('suspicious', background='#ffcccc')
            self.tree.tag_configure('high_usage', background='#fff0cc')
            self.tree.tag_configure('zombie', background='#ccffcc')
            
            self.process_count_label.config(text=f"Processes: {len(processes)}")
            self.high_usage_label.config(text=f"High Usage: {high_usage_count}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh processes: {e}")
    
    def update_category_counts(self, processes):
        """Update counts for each process category"""
        # Reset counts
        self.category_counts = {key: 0 for key in self.category_counts}
        
        for proc in processes:
            try:
                categories = self.categorizer.categorize_process(proc)
                for category in categories:
                    if category in self.category_counts:
                        self.category_counts[category] += 1
            except:
                self.category_counts['unknown'] += 1
    
    def update_top_processes(self, processes):
        """Update top processes by CPU usage"""
        # Sort processes by CPU usage
        sorted_processes = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]
        
        # Clear existing items
        for item in self.top_tree.get_children():
            self.top_tree.delete(item)
        
        # Add top processes
        for proc in sorted_processes:
            self.top_tree.insert('', 'end', values=(
                proc['name'][:30],
                f"{proc.get('cpu_percent', 0):.1f}",
                f"{proc.get('memory_percent', 0):.2f}",
                proc['pid']
            ))
    
    def update_system_stats(self, stats):
        """Update system statistics display"""
        self.cpu_label.config(text=f"CPU: {stats['cpu_percent']:.1f}%")
        self.memory_label.config(text=f"Memory: {stats['memory_percent']:.1f}% ({stats['memory_used_gb']}GB/{stats['memory_total_gb']}GB)")
        
        battery_text = f"Battery: {stats['battery_percent']}%" if stats.get('battery_percent') else "Battery: N/A"
        self.battery_label.config(text=battery_text)
        
        # Update system info in overview tab
        self.update_system_info()
    
    def update_system_info(self):
        """Update system information in overview tab"""
        try:
            # OS information
            import platform
            self.os_label.config(text=f"OS: {platform.system()} {platform.release()}")
            
            # CPU information
            cpu_cores = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            freq_text = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A"
            self.cpu_info_label.config(text=f"CPU Cores: {cpu_cores}, Frequency: {freq_text}")
            
            # Memory information
            memory = psutil.virtual_memory()
            total_memory_gb = memory.total / (1024**3)
            self.memory_info_label.config(text=f"Total Memory: {total_memory_gb:.1f} GB")
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            self.disk_info_label.config(text=f"Disk Usage: {disk_usage:.1f}%")
            
        except Exception as e:
            print(f"Error updating system info: {e}")
    
    def on_process_select(self, event):
        """Handle process selection"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            self.show_process_details(values[0])  # PID
    
    def show_process_details(self, pid):
        """Show detailed process information"""
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Process Details - PID {pid}")
        detail_window.geometry("500x400")
        
        try:
            process = psutil.Process(int(pid))
            with process.oneshot():
                info = process.as_dict(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                      'status', 'username', 'create_time', 'exe', 'ppid', 'num_threads'])
                
            # Create text widget for details
            text_frame = tk.Frame(detail_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
            text_widget.config(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Add process info
            for key, value in info.items():
                text_widget.insert(tk.END, f"{key}: {value}\n\n")
            
            text_widget.config(state=tk.DISABLED)
                
        except psutil.NoSuchProcess:
            tk.Label(detail_window, text="Process no longer exists").pack(padx=10, pady=10)
    
    def terminate_selected(self):
        """Terminate selected process"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            pid = int(self.tree.item(item, 'values')[0])
            name = self.tree.item(item, 'values')[1]
            
            if messagebox.askyesno("Confirm", f"Terminate process {name} (PID: {pid})?"):
                try:
                    process = psutil.Process(pid)
                    process.terminate()
                    self.refresh_processes()
                    messagebox.showinfo("Success", f"Process {name} terminated")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to terminate process: {e}")
    
    def auto_clean(self):
        """Automatically clean problematic processes"""
        processes = self.process_collector.get_all_processes()
        terminated_count = 0
        
        for proc in processes:
            categories = self.categorizer.categorize_process(proc)
            
            # Auto-terminate zombies if enabled
            if ('zombie' in categories and 
                self.config.config['auto_terminate_zombies']):
                try:
                    psutil.Process(proc['pid']).terminate()
                    terminated_count += 1
                except:
                    pass
        
        self.refresh_processes()
        messagebox.showinfo("Auto Clean", f"Terminated {terminated_count} zombie processes")
    
    def toggle_monitoring(self):
        """Toggle real-time monitoring"""
        if not self.running:
            self.running = True
            self.monitor_btn.config(text="Stop Monitoring")
            
            # Start chart animation
            self.animation = animation.FuncAnimation(self.cpu_fig, self.update_charts, interval=1000, blit=False)
            
            self.update_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.update_thread.start()
        else:
            self.running = False
            self.monitor_btn.config(text="Start Monitoring")
            
            # Stop animation
            if self.animation:
                self.animation.event_source.stop()
    
    def monitoring_loop(self):
        """Real-time monitoring loop"""
        while self.running:
            self.refresh_processes()
            time.sleep(2)  # Update every 2 seconds
    
    def open_settings(self):
        """Open settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        
        tk.Label(settings_window, text="Configuration Settings", 
                font=("Arial", 12, "bold")).pack(pady=10)
        
        # Add settings controls here
        tk.Label(settings_window, text="Settings will be implemented here").pack(pady=20)
    
    def run(self):
        """Start the application"""
        self.refresh_processes()
        self.update_system_info()
        self.root.mainloop()