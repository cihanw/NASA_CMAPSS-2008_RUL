import pandas as pd
import os

def analyze_shortest_sequence(file_path):
    print(f"\nAnalyzing: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        # Read only first two columns: unit_nr, time_cycles
        df = pd.read_csv(file_path, sep=r'\s+', header=None, usecols=[0, 1], names=['unit_nr', 'time_cycles'])
        
        # Calculate max cycle for each unit
        max_cycles = df.groupby('unit_nr')['time_cycles'].max()
        
        # Find the minimum of these max cycles
        min_life = max_cycles.min()
        min_life_units = max_cycles[max_cycles == min_life].index.tolist()
        
        print(f"Total Number of Unique Units: {len(max_cycles)}")
        print(f"Minimum Sequence Length: {min_life}")
        print(f"Unit ID(s) with minimum length: {min_life_units}")
        
        # Stats summary
        print(f"Descriptive Statistics for Sequence Lengths:")
        print(max_cycles.describe())
        
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

# Define paths
train_path = os.path.join('data', 'raw', 'train_FD004.txt')
test_path = os.path.join('data', 'raw', 'test_FD004.txt')

# Run analysis
analyze_shortest_sequence(train_path)
analyze_shortest_sequence(test_path)
