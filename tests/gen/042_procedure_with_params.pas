procedure p(a, b: integer; c: real);
begin
  writeln(a);
  writeln(b);
  writeln(c);
end;

var
  z: integer;

begin
  z := 66;
  p(66, 18, 172.34);
  p(28, z, 98.54);
end.