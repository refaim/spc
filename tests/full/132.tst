var
  arr: array[1..2] of array[1..3] of record
    arr: array[0..3] of record
      inner: integer;
    end;
  end;

begin
  arr[1][2].arr[0].inner;
end.