var
  a: array[1..20] of integer;
  i, j, index, size: integer;
begin
  size := 20;
  for i := 1 to size do a[i] := -i;

  for i := 1 to size do begin
    index := a[i];
    j := i;
    while ((j > 1) and (a[j-1] > index)) do begin
        a[j] := a[j-1];
        j := j - 1;
    end;;
    a[j] := index;
  end;;

  for i := 1 to size do writeln(a[i]);
end.