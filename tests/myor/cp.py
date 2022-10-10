from ortools.sat.python import cp_model
# Creates the model.
model = cp_model.CpModel()

# Creates the variables.
num_vals = 3
x = model.NewIntVar(0, num_vals - 1, 'x')
y = model.NewIntVar(0, num_vals - 1, 'y')
z = model.NewIntVar(0, num_vals - 1, 'z')

# Creates the constraints.
model.Add(x != y)

# Creates a solver and solves the model.
solver = cp_model.CpSolver()
status = solver.Solve(model)
print('status = %i' % status)
print('x = %i' % solver.Value(x))
print('y = %i' % solver.Value(y))
print('z = %i' % solver.Value(z))
