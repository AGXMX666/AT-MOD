import csv
import random
import string
import argparse


def generate_registration_codes(num_codes):
    filename = "registration_codes.csv"
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["codes", "user", "Status", "time"])
        for _ in range(num_codes):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
            writer.writerow([code, "", "0", ""])

    print(f"成功生成 {num_codes} 个注册码，并保存到 {filename}")

def main():
    parser = argparse.ArgumentParser(description="生成注册码")
    parser.add_argument('-n', '--num', type=int, help='生成注册码数量')
    args = parser.parse_args()
    if args.num is not None:
        num = args.num
    else:
        while True:
            try:
                num = int(input("请输入要生成的注册码数量: "))
                if num > 0:
                    break
                else:
                    print("请输入大于0的整数！")
            except ValueError:
                print("请输入有效的整数！")
    generate_registration_codes(num)

if __name__ == "__main__":
    main()