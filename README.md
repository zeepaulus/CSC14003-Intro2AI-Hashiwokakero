# Hashiwokakero Solver

## Project Structure
The project is organized as follows:
```
HASHIWOKAKERO/
│
├── README.md               # Project documentation and usage guide.
│
└── Source/                 # Main source code directory.
    │
    ├── Inputs/             # Directory containing input puzzle files (.txt).
    │   ├── input-01.txt    
    │   ├── input-02.txt
    │   └── ...
    │
    ├── Outputs/            # Directory storing solving results and benchmark charts.
    │   ├── Benchmark/      
    │   ├── PySAT/         
    │   ├── AStar/             
    │   ├── Backtracking/   
    │   └── BruteForce/     
    │
    ├── gui.py              
    ├── benchmark.py        
    ├── utils.py            
    ├── solve_pysat.py      
    ├── solve_astar.py      
    ├── solve_backtracking.py 
    ├── solve_bruteforce.py 
    └── requirements.txt    
```

## How to Run the Code
Before running the code, ensure you have Python 3.8 or higher installed.
### 1. Clone repository:
```bash
git clone <repository-url>
cd CSC14003-Intro2AI-Hashiwokakero
```

### 2. Install Dependencies

From the `Source` folder, install the required libraries:

```bash
cd Source
pip install -r requirements.txt
```

### 3. Run the Application

Execute the main GUI program:

```bash
python gui.py
```
