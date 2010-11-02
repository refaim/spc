function f(x: integer; y: real): integer;
begin
  writeln(x);
  writeln(y);
  Result := x;
  writeln(x);
  writeln(y);
  writeln(-1);
end;

begin
  writeln(f(99, 67.4));
end.