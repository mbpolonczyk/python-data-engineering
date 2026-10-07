# 3.1 Reading and writing files

# Exercise1: Open orders.txt
with open(
    "src/day3/orders.txt", "r"
) as file:  # safely opens and automatically closes the file
    content = file.read()  # returns one string

print(content)

# Exercise2: Read the orders line by line
with open("src/day3/orders.txt", "r") as file:
    content = file.readlines()  # returns a list of strings

print(content)

# Exercise3: Process each order
for line in content:
    print(line.strip())  # strip removes newline (blank lines between orders made by \n)

# Exercise4: Extract the order ID and value
for line in content:
    parts = line.strip().split(",")
    print(parts)

# Exercise5: Modify the loop
for line in content:
    order_id, value = line.strip().split(",")
    value = int(value)
    print(order_id, value)

# Exercise6: Calculate the total
total = 0
for line in content:
    order_id, value = line.strip().split(",")
    value = int(value)
    total += value
print(total)


# Exercise7: Turn it into a function
def calculate_total_from_file(filename):

    total = 0

    with open(filename, "r") as file:
        for line in file:
            order_id, value = line.strip().split(",")
            total += int(value)
    return total


total = calculate_total_from_file("src/day3/orders.txt")
print(total)


# Exercise8: Create a function def calculate_and_save_total(input_file, output_file)
def calculate_and_save_total(input_file, output_file):

    total = 0

    with open(input_file, "r") as file:
        for line in file:
            order_id, value = line.strip().split(",")
            total += int(value)
    with open(output_file, "w") as file:
        file.write(f"Total order value: {total}")
    return total


total = calculate_and_save_total("src/day3/orders.txt", "src/day3/total.txt")
print(total)

# Exercise9: Write code that appends to total.txt
with open("src/day3/total.txt", "a") as file:
    file.write("\nCalculation completed.")  # \n so it starts on a new line


# Exercise10
def calculate_and_save_total_and_count(input_file, output_file):

    total = 0
    order_count = 0

    with open(input_file, "r") as file:
        for line in file:
            order_id, value = line.strip().split(",")
            total += int(value)
            order_count += 1
    with open(output_file, "w") as file:
        file.write(f"Total order value: {total}")
        file.write(f"\nNumber of orders: {order_count}")
    return total


calculate_and_save_total_and_count("src/day3/orders.txt", "src/day3/total.txt")
