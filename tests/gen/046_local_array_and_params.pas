procedure p(a, b: integer);
var
  x, y: integer;
  arr: array[1..10] of integer;
begin
  x := a + 1;
  y := b + 1;
  writeln(x);
  writeln(y);
  writeln(a);
  writeln(b);
  arr[5] := 18;
  writeln(arr[5]);
  writeln(x);
  writeln(y);
  writeln(a);
  writeln(b);
end;

begin
  p(10, 20);
end.