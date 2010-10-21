var
  a: array[1..10] of real;
  i, j: integer;
  t: real;
begin
  for i := 1 to 10 do a[i] := i / 2;

  for i := 1 to 10 do
    for j := i + 1 to 10 do
      if a[i] < a[j] then begin
        t := a[i];
        a[i] := a[j];
        a[j] := t;
      end;;

  for i := 1 to 10 do writeln(a[i]);
end.