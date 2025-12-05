package main

import (
	"fmt"
	"log"
	"os"

	"golang.org/x/crypto/bcrypt"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run main.go <new_password>")
		fmt.Println("Example: go run main.go myNewPassword123")
		os.Exit(1)
	}

	password := os.Args[1]
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		log.Fatal("Failed to hash password:", err)
	}

	fmt.Println("Generated bcrypt hash for password:", password)
	fmt.Println("")
	fmt.Println("Run this SQL to update the user:")
	fmt.Printf("UPDATE users SET password = '%s' WHERE email = 'okoinvestments@gmail.com';\n", string(hashedPassword))
}
