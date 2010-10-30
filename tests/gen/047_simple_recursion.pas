procedure p(x: integer);
begin
  if x > 0 then p(x - 1);
  writeln(x);
end;

begin
  p(10);
end.
