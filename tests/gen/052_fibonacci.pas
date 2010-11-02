function fib(n: integer): integer;
begin
    if (n = 0) or (n = 1) then
        result := n
    else
        result := fib(n - 1) + fib(n - 2);
    n := 1;
end;

var
  i: integer;
begin
  for i := 0 to 20 do writeln(fib(i));
end.