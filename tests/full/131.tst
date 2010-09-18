var
  arr: array[1..2] of array[1..3] of record
    f: integer;
  end;

begin
  arr[1][2].f;
end.