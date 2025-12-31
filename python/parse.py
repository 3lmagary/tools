import argparse
import sys

def main():
    # إنشاء الـ Parser مع وصف واضح للأداة
    parser = argparse.ArgumentParser(
        description="Credentials Handler - A simple tool to manage user and password inputs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # إضافة الـ Arguments
    # الـ help بيخلي المستخدم يعرف كل Flag بيعمل إيه لما يكتب -h
    parser.add_argument("-u", "--user", type=str, help="Username for authentication", default="admin")
    parser.add_argument("-p", "--password", type=str, required=True, help="Password for authentication (Required)")

    # قراءة المدخلات
    args = parser.parse_args()

    # طباعة النتائج بشكل منظم
    print(f"[*] Identity: {args.user}")
    print(f"[*] Credential: {args.password}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
        sys.exit(1)