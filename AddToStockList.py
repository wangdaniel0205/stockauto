def write_to_file(t):
    f = open("stock_list.txt", "a")
    f.write(" {}".format(t))
    f.close()

def read_target_stocks():
    f = open("stock_list.txt", "r")
    stocks = f.read().split(" ")
    return stocks

if __name__ == '__main__': 
    stocks = read_target_stocks()

    while True:
        newStock = input()
        if not(newStock in stocks):
            stocks.append(newStock)
            write_to_file(newStock)
