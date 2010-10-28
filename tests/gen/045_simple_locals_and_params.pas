procedure p(a, b: integer; c: real);
var
  x, y: real;
  z: integer;
begin
  x := c;
  y := 88.88;
  z := a + b - 15;
  writeln(x);
  writeln(y);
  writeln(z);
end;

begin
  p(10, 20, 66.77);
end.