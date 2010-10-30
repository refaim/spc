var
  A: array[1..100] of integer;
  i: integer;

procedure QuickSort(iLo, iHi: Integer);
var
  Lo, Hi, Pivot, T: Integer;
begin
  Lo := iLo;
  Hi := iHi;
  Pivot := A[(Lo + Hi) div 2];
  repeat begin
    while A[Lo] < Pivot do Lo := Lo + 1;
    while A[Hi] > Pivot do Hi := Hi - 1;
    if Lo <= Hi then
    begin
      T := A[Lo];
      A[Lo] := A[Hi];
      A[Hi] := T;
      Lo := Lo + 1;
      Hi := Hi - 1;
    end;
  end until Lo > Hi;
  if Hi > iLo then QuickSort(iLo, Hi);
  if Lo < iHi then QuickSort(Lo, iHi);
end;

begin
  for i := 1 to 100 do
    if i mod 2 = 0 
    then 
        A[i] := -i
    else
        A[i] := i;

  QuickSort(1, 100);

  for i := 1 to 100 do writeln(A[i]); 
end.
