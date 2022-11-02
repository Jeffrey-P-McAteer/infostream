

pub fn test_01() -> usize {
  use url::Url;

  let input: &'static str = "is://username@example.com/database-name/table-name[10]";
  
  let result = Url::parse(input).unwrap();
  
  println!("result={:?}", result);

  assert_eq!(result.scheme(), "is");
  assert_eq!(result.host(), Some(url::Host::Domain("example.com")));
  assert_eq!(result.username(), "username");
  assert_eq!(result.path(), "/database-name/table-name[10]");


  1
}

