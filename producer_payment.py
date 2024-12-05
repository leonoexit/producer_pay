# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import pandas as pd
from tksheet import Sheet

def convert_to_number(value):
    if pd.isna(value) or value == "":
        return 0
    if isinstance(value, (int, float)):
        return value
    # Remove commas and convert to float
    try:
        return float(str(value).replace(",", ""))
    except:
        return 0

class ProducerPaymentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bảng tính chi phí External Producer") ")
        self.root.geometry("1200x800")

        # Main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create frames for detail and summary tables
        self.detail_frame = ttk.LabelFrame(self.main_frame, text="Chi tiết")
        self.detail_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Buttons frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill="x", padx=5, pady=2)
        
        # Add/Remove row buttons
        self.add_row_btn = ttk.Button(self.button_frame, text="Thêm dòng", command=self.add_row)
        self.add_row_btn.pack(side="left", padx=5)
        
        self.remove_row_btn = ttk.Button(self.button_frame, text="Xóa dòng", command=self.remove_row)
        self.remove_row_btn.pack(side="left", padx=5)

        self.summary_frame = ttk.LabelFrame(self.main_frame, text="Tổng hợp")
        self.summary_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Initialize tables
        self.setup_detail_table()
        self.setup_summary_table()

        # Create calculate button
        self.calc_button = ttk.Button(self.main_frame, text="Tính toán", command=self.calculate)
        self.calc_button.pack(pady=5)

    def setup_detail_table(self):
        self.detail_sheet = Sheet(self.detail_frame,
                                headers=["Producer", "Sản phẩm", "Quality", "Real Cost", 
                                       "Producer Pay", "Manager Pay", "No Manager Pay"],
                                height=300)
        self.detail_sheet.enable_bindings()
        self.detail_sheet.pack(fill="both", expand=True)
        
        # Set column widths
        for col in range(7):
            self.detail_sheet.column_width(column=col, width=150)
        
        # Initialize with 10 empty rows
        self.detail_sheet.set_sheet_data([[""]*6 + ["0"] for _ in range(10)])
        
        # Enable copy/paste
        self.detail_sheet.enable_bindings(("copy", "paste"))
        
        # Set column types
        self.detail_sheet.set_column_data(2, ["1" for _ in range(10)])  # Quality default to 1
        
        # Add double click binding for No Manager Pay column
        self.detail_sheet.bind("<Double-Button-1>", self.toggle_manager_pay)

    def toggle_manager_pay(self, event):
        try:
            clicked_row = self.detail_sheet.identify_row(event)
            clicked_col = self.detail_sheet.identify_col(event)
            
            # Check if clicked on No Manager Pay column (index 6)
            if clicked_col == 6:
                current_value = self.detail_sheet.get_cell_data(clicked_row, clicked_col)
                # Toggle between "0" and "1"
                new_value = "1" if current_value == "0" else "0"
                self.detail_sheet.set_cell_data(clicked_row, clicked_col, new_value)
        except:
            pass

    def setup_summary_table(self):
        self.summary_sheet = Sheet(self.summary_frame,
                                 headers=["Producer", "Total Quality", "Total Real Cost", 
                                        "Total Producer Pay", "Total Manager Pay"],
                                 height=200)
        self.summary_sheet.enable_bindings()
        self.summary_sheet.pack(fill="both", expand=True)
        
        # Set column widths
        for col in range(5):
            self.summary_sheet.column_width(column=col, width=180)

    def add_row(self):
        current_data = self.detail_sheet.get_sheet_data()
        current_data.append(["", "", "1", "", "", "", "0"])
        self.detail_sheet.set_sheet_data(current_data)

    def remove_row(self):
        selected_rows = self.detail_sheet.get_selected_rows()
        if not selected_rows:
            return
            
        current_data = self.detail_sheet.get_sheet_data()
        new_data = [row for idx, row in enumerate(current_data) if idx not in selected_rows]
        self.detail_sheet.set_sheet_data(new_data)

    def format_number(self, value):
        if pd.isna(value) or value == 0:
            return ""
        return f"{value:,.0f}"

    def calculate(self):
        # Get data from detail sheet
        data = self.detail_sheet.get_sheet_data()
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=["Producer", "Product", "Quality", "Real Cost", 
                                       "Producer Pay", "Manager Pay", "No Manager Pay"])
        
        # Remove empty rows
        df = df[df["Producer"].astype(str).str.strip() != ""]
        
        # Convert numeric columns
        df["Quality"] = df["Quality"].apply(convert_to_number)
        df["Real Cost"] = df["Real Cost"].apply(convert_to_number)
        df["No Manager Pay"] = df["No Manager Pay"].map({"1": True, "0": False})
        
        # Calculate payments
        for idx in df.index:
            base_cost = float(df.at[idx, "Real Cost"])  # This is the base cost per unit
            quality = float(df.at[idx, "Quality"])
            no_manager_pay = df.at[idx, "No Manager Pay"]
            
            # Calculate final real cost based on quality
            real_cost = base_cost * quality
            
            if no_manager_pay:
                # If No Manager Pay is checked, producer gets all
                producer_pay = real_cost
                manager_pay = 0
            else:
                # Calculate producer pay first
                producer_pay = real_cost - (50000 * quality)
                # Ensure producer_pay doesn't go negative
                if producer_pay < 0:
                    producer_pay = 0
                
                # Manager gets the difference
                manager_pay = real_cost - producer_pay
            
            # Update real cost with the final amount
            df.at[idx, "Real Cost"] = real_cost
            df.at[idx, "Producer Pay"] = producer_pay
            df.at[idx, "Manager Pay"] = manager_pay

        # Format numbers for display
        df["Real Cost"] = df["Real Cost"].apply(self.format_number)
        df["Producer Pay"] = df["Producer Pay"].apply(self.format_number)
        df["Manager Pay"] = df["Manager Pay"].apply(self.format_number)

        # Update detail sheet with calculated values
        all_data = self.detail_sheet.get_sheet_data()
        for idx, row in df.iterrows():
            row["No Manager Pay"] = "1" if row["No Manager Pay"] else "0"
            all_data[idx] = row.tolist()
        self.detail_sheet.set_sheet_data(all_data)

        # Calculate summary (using numeric values before formatting)
        df["Real Cost"] = df["Real Cost"].apply(convert_to_number)
        df["Producer Pay"] = df["Producer Pay"].apply(convert_to_number)
        df["Manager Pay"] = df["Manager Pay"].apply(convert_to_number)
        
        summary = df.groupby("Producer").agg({
            "Quality": "sum",
            "Real Cost": "sum",
            "Producer Pay": "sum",
            "Manager Pay": "sum"
        }).reset_index()

        # Format summary numbers
        for col in ["Real Cost", "Producer Pay", "Manager Pay"]:
            summary[col] = summary[col].apply(self.format_number)

        # Update summary sheet
        self.summary_sheet.set_sheet_data(summary.values.tolist())

if __name__ == "__main__":
    root = tk.Tk()
    app = ProducerPaymentApp(root)
    root.mainloop()
