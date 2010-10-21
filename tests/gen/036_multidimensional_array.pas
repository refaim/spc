var
  a: array[1..2] of array [1..5] of integer;
  i, j: integer;
begin
  for i := 1 to 2 do
    for j := 1 to 5 do begin
      a[i][j] := i + j;
      writeln(a[i][j] = i + j);
    end;
end.