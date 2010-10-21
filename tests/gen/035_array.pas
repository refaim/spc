var
  a: array[1..10] of integer;
begin
  a[1] := 16;
  a[10] := 32 + a[1];
  writeln(a[1] + a[10]);
end.