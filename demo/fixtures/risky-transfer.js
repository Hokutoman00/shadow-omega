function transfer(user, target, amount) {
  if (user.balance >= amount) {
    target.balance += amount;
    user.balance -= amount;
  }
}
