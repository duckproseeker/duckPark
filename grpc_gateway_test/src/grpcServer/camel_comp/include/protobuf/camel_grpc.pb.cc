// Generated by the protocol buffer compiler.  DO NOT EDIT!
// source: camel_grpc.proto

#include "camel_grpc.pb.h"

#include <algorithm>

#include <google/protobuf/io/coded_stream.h>
#include <google/protobuf/extension_set.h>
#include <google/protobuf/wire_format_lite.h>
#include <google/protobuf/descriptor.h>
#include <google/protobuf/generated_message_reflection.h>
#include <google/protobuf/reflection_ops.h>
#include <google/protobuf/wire_format.h>
// @@protoc_insertion_point(includes)
#include <google/protobuf/port_def.inc>

PROTOBUF_PRAGMA_INIT_SEG

namespace _pb = ::PROTOBUF_NAMESPACE_ID;
namespace _pbi = _pb::internal;

namespace camel {
namespace api {
PROTOBUF_CONSTEXPR GamepadControl::GamepadControl(
    ::_pbi::ConstantInitialized): _impl_{
    /*decltype(_impl_.force_)*/false
  , /*decltype(_impl_._cached_size_)*/{}} {}
struct GamepadControlDefaultTypeInternal {
  PROTOBUF_CONSTEXPR GamepadControlDefaultTypeInternal()
      : _instance(::_pbi::ConstantInitialized{}) {}
  ~GamepadControlDefaultTypeInternal() {}
  union {
    GamepadControl _instance;
  };
};
PROTOBUF_ATTRIBUTE_NO_DESTROY PROTOBUF_CONSTINIT PROTOBUF_ATTRIBUTE_INIT_PRIORITY1 GamepadControlDefaultTypeInternal _GamepadControl_default_instance_;
PROTOBUF_CONSTEXPR Token::Token(
    ::_pbi::ConstantInitialized): _impl_{
    /*decltype(_impl_.key_)*/{&::_pbi::fixed_address_empty_string, ::_pbi::ConstantInitialized{}}
  , /*decltype(_impl_.result_)*/nullptr
  , /*decltype(_impl_._cached_size_)*/{}} {}
struct TokenDefaultTypeInternal {
  PROTOBUF_CONSTEXPR TokenDefaultTypeInternal()
      : _instance(::_pbi::ConstantInitialized{}) {}
  ~TokenDefaultTypeInternal() {}
  union {
    Token _instance;
  };
};
PROTOBUF_ATTRIBUTE_NO_DESTROY PROTOBUF_CONSTINIT PROTOBUF_ATTRIBUTE_INIT_PRIORITY1 TokenDefaultTypeInternal _Token_default_instance_;
PROTOBUF_CONSTEXPR Result::Result(
    ::_pbi::ConstantInitialized): _impl_{
    /*decltype(_impl_.message_)*/{&::_pbi::fixed_address_empty_string, ::_pbi::ConstantInitialized{}}
  , /*decltype(_impl_.errorcode_)*/0
  , /*decltype(_impl_._cached_size_)*/{}} {}
struct ResultDefaultTypeInternal {
  PROTOBUF_CONSTEXPR ResultDefaultTypeInternal()
      : _instance(::_pbi::ConstantInitialized{}) {}
  ~ResultDefaultTypeInternal() {}
  union {
    Result _instance;
  };
};
PROTOBUF_ATTRIBUTE_NO_DESTROY PROTOBUF_CONSTINIT PROTOBUF_ATTRIBUTE_INIT_PRIORITY1 ResultDefaultTypeInternal _Result_default_instance_;
}  // namespace api
}  // namespace camel
static ::_pb::Metadata file_level_metadata_camel_5fgrpc_2eproto[3];
static constexpr ::_pb::EnumDescriptor const** file_level_enum_descriptors_camel_5fgrpc_2eproto = nullptr;
static constexpr ::_pb::ServiceDescriptor const** file_level_service_descriptors_camel_5fgrpc_2eproto = nullptr;

const uint32_t TableStruct_camel_5fgrpc_2eproto::offsets[] PROTOBUF_SECTION_VARIABLE(protodesc_cold) = {
  ~0u,  // no _has_bits_
  PROTOBUF_FIELD_OFFSET(::camel::api::GamepadControl, _internal_metadata_),
  ~0u,  // no _extensions_
  ~0u,  // no _oneof_case_
  ~0u,  // no _weak_field_map_
  ~0u,  // no _inlined_string_donated_
  PROTOBUF_FIELD_OFFSET(::camel::api::GamepadControl, _impl_.force_),
  ~0u,  // no _has_bits_
  PROTOBUF_FIELD_OFFSET(::camel::api::Token, _internal_metadata_),
  ~0u,  // no _extensions_
  ~0u,  // no _oneof_case_
  ~0u,  // no _weak_field_map_
  ~0u,  // no _inlined_string_donated_
  PROTOBUF_FIELD_OFFSET(::camel::api::Token, _impl_.key_),
  PROTOBUF_FIELD_OFFSET(::camel::api::Token, _impl_.result_),
  ~0u,  // no _has_bits_
  PROTOBUF_FIELD_OFFSET(::camel::api::Result, _internal_metadata_),
  ~0u,  // no _extensions_
  ~0u,  // no _oneof_case_
  ~0u,  // no _weak_field_map_
  ~0u,  // no _inlined_string_donated_
  PROTOBUF_FIELD_OFFSET(::camel::api::Result, _impl_.errorcode_),
  PROTOBUF_FIELD_OFFSET(::camel::api::Result, _impl_.message_),
};
static const ::_pbi::MigrationSchema schemas[] PROTOBUF_SECTION_VARIABLE(protodesc_cold) = {
  { 0, -1, -1, sizeof(::camel::api::GamepadControl)},
  { 7, -1, -1, sizeof(::camel::api::Token)},
  { 15, -1, -1, sizeof(::camel::api::Result)},
};

static const ::_pb::Message* const file_default_instances[] = {
  &::camel::api::_GamepadControl_default_instance_._instance,
  &::camel::api::_Token_default_instance_._instance,
  &::camel::api::_Result_default_instance_._instance,
};

const char descriptor_table_protodef_camel_5fgrpc_2eproto[] PROTOBUF_SECTION_VARIABLE(protodesc_cold) =
  "\n\020camel_grpc.proto\022\tcamel.api\"\037\n\016Gamepad"
  "Control\022\r\n\005force\030\001 \001(\010\"7\n\005Token\022\013\n\003key\030\001"
  " \001(\t\022!\n\006result\030\002 \001(\0132\021.camel.api.Result\""
  ",\n\006Result\022\021\n\terrorCode\030\001 \001(\005\022\017\n\007message\030"
  "\002 \001(\0142N\n\nAgvService\022@\n\021ApplyStickControl"
  "\022\031.camel.api.GamepadControl\032\020.camel.api."
  "Tokenb\006proto3"
  ;
static ::_pbi::once_flag descriptor_table_camel_5fgrpc_2eproto_once;
const ::_pbi::DescriptorTable descriptor_table_camel_5fgrpc_2eproto = {
    false, false, 253, descriptor_table_protodef_camel_5fgrpc_2eproto,
    "camel_grpc.proto",
    &descriptor_table_camel_5fgrpc_2eproto_once, nullptr, 0, 3,
    schemas, file_default_instances, TableStruct_camel_5fgrpc_2eproto::offsets,
    file_level_metadata_camel_5fgrpc_2eproto, file_level_enum_descriptors_camel_5fgrpc_2eproto,
    file_level_service_descriptors_camel_5fgrpc_2eproto,
};
PROTOBUF_ATTRIBUTE_WEAK const ::_pbi::DescriptorTable* descriptor_table_camel_5fgrpc_2eproto_getter() {
  return &descriptor_table_camel_5fgrpc_2eproto;
}

// Force running AddDescriptors() at dynamic initialization time.
PROTOBUF_ATTRIBUTE_INIT_PRIORITY2 static ::_pbi::AddDescriptorsRunner dynamic_init_dummy_camel_5fgrpc_2eproto(&descriptor_table_camel_5fgrpc_2eproto);
namespace camel {
namespace api {

// ===================================================================

class GamepadControl::_Internal {
 public:
};

GamepadControl::GamepadControl(::PROTOBUF_NAMESPACE_ID::Arena* arena,
                         bool is_message_owned)
  : ::PROTOBUF_NAMESPACE_ID::Message(arena, is_message_owned) {
  SharedCtor(arena, is_message_owned);
  // @@protoc_insertion_point(arena_constructor:camel.api.GamepadControl)
}
GamepadControl::GamepadControl(const GamepadControl& from)
  : ::PROTOBUF_NAMESPACE_ID::Message() {
  GamepadControl* const _this = this; (void)_this;
  new (&_impl_) Impl_{
      decltype(_impl_.force_){}
    , /*decltype(_impl_._cached_size_)*/{}};

  _internal_metadata_.MergeFrom<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(from._internal_metadata_);
  _this->_impl_.force_ = from._impl_.force_;
  // @@protoc_insertion_point(copy_constructor:camel.api.GamepadControl)
}

inline void GamepadControl::SharedCtor(
    ::_pb::Arena* arena, bool is_message_owned) {
  (void)arena;
  (void)is_message_owned;
  new (&_impl_) Impl_{
      decltype(_impl_.force_){false}
    , /*decltype(_impl_._cached_size_)*/{}
  };
}

GamepadControl::~GamepadControl() {
  // @@protoc_insertion_point(destructor:camel.api.GamepadControl)
  if (auto *arena = _internal_metadata_.DeleteReturnArena<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>()) {
  (void)arena;
    return;
  }
  SharedDtor();
}

inline void GamepadControl::SharedDtor() {
  GOOGLE_DCHECK(GetArenaForAllocation() == nullptr);
}

void GamepadControl::SetCachedSize(int size) const {
  _impl_._cached_size_.Set(size);
}

void GamepadControl::Clear() {
// @@protoc_insertion_point(message_clear_start:camel.api.GamepadControl)
  uint32_t cached_has_bits = 0;
  // Prevent compiler warnings about cached_has_bits being unused
  (void) cached_has_bits;

  _impl_.force_ = false;
  _internal_metadata_.Clear<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>();
}

const char* GamepadControl::_InternalParse(const char* ptr, ::_pbi::ParseContext* ctx) {
#define CHK_(x) if (PROTOBUF_PREDICT_FALSE(!(x))) goto failure
  while (!ctx->Done(&ptr)) {
    uint32_t tag;
    ptr = ::_pbi::ReadTag(ptr, &tag);
    switch (tag >> 3) {
      // bool force = 1;
      case 1:
        if (PROTOBUF_PREDICT_TRUE(static_cast<uint8_t>(tag) == 8)) {
          _impl_.force_ = ::PROTOBUF_NAMESPACE_ID::internal::ReadVarint64(&ptr);
          CHK_(ptr);
        } else
          goto handle_unusual;
        continue;
      default:
        goto handle_unusual;
    }  // switch
  handle_unusual:
    if ((tag == 0) || ((tag & 7) == 4)) {
      CHK_(ptr);
      ctx->SetLastTag(tag);
      goto message_done;
    }
    ptr = UnknownFieldParse(
        tag,
        _internal_metadata_.mutable_unknown_fields<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(),
        ptr, ctx);
    CHK_(ptr != nullptr);
  }  // while
message_done:
  return ptr;
failure:
  ptr = nullptr;
  goto message_done;
#undef CHK_
}

uint8_t* GamepadControl::_InternalSerialize(
    uint8_t* target, ::PROTOBUF_NAMESPACE_ID::io::EpsCopyOutputStream* stream) const {
  // @@protoc_insertion_point(serialize_to_array_start:camel.api.GamepadControl)
  uint32_t cached_has_bits = 0;
  (void) cached_has_bits;

  // bool force = 1;
  if (this->_internal_force() != 0) {
    target = stream->EnsureSpace(target);
    target = ::_pbi::WireFormatLite::WriteBoolToArray(1, this->_internal_force(), target);
  }

  if (PROTOBUF_PREDICT_FALSE(_internal_metadata_.have_unknown_fields())) {
    target = ::_pbi::WireFormat::InternalSerializeUnknownFieldsToArray(
        _internal_metadata_.unknown_fields<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(::PROTOBUF_NAMESPACE_ID::UnknownFieldSet::default_instance), target, stream);
  }
  // @@protoc_insertion_point(serialize_to_array_end:camel.api.GamepadControl)
  return target;
}

size_t GamepadControl::ByteSizeLong() const {
// @@protoc_insertion_point(message_byte_size_start:camel.api.GamepadControl)
  size_t total_size = 0;

  uint32_t cached_has_bits = 0;
  // Prevent compiler warnings about cached_has_bits being unused
  (void) cached_has_bits;

  // bool force = 1;
  if (this->_internal_force() != 0) {
    total_size += 1 + 1;
  }

  return MaybeComputeUnknownFieldsSize(total_size, &_impl_._cached_size_);
}

const ::PROTOBUF_NAMESPACE_ID::Message::ClassData GamepadControl::_class_data_ = {
    ::PROTOBUF_NAMESPACE_ID::Message::CopyWithSourceCheck,
    GamepadControl::MergeImpl
};
const ::PROTOBUF_NAMESPACE_ID::Message::ClassData*GamepadControl::GetClassData() const { return &_class_data_; }


void GamepadControl::MergeImpl(::PROTOBUF_NAMESPACE_ID::Message& to_msg, const ::PROTOBUF_NAMESPACE_ID::Message& from_msg) {
  auto* const _this = static_cast<GamepadControl*>(&to_msg);
  auto& from = static_cast<const GamepadControl&>(from_msg);
  // @@protoc_insertion_point(class_specific_merge_from_start:camel.api.GamepadControl)
  GOOGLE_DCHECK_NE(&from, _this);
  uint32_t cached_has_bits = 0;
  (void) cached_has_bits;

  if (from._internal_force() != 0) {
    _this->_internal_set_force(from._internal_force());
  }
  _this->_internal_metadata_.MergeFrom<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(from._internal_metadata_);
}

void GamepadControl::CopyFrom(const GamepadControl& from) {
// @@protoc_insertion_point(class_specific_copy_from_start:camel.api.GamepadControl)
  if (&from == this) return;
  Clear();
  MergeFrom(from);
}

bool GamepadControl::IsInitialized() const {
  return true;
}

void GamepadControl::InternalSwap(GamepadControl* other) {
  using std::swap;
  _internal_metadata_.InternalSwap(&other->_internal_metadata_);
  swap(_impl_.force_, other->_impl_.force_);
}

::PROTOBUF_NAMESPACE_ID::Metadata GamepadControl::GetMetadata() const {
  return ::_pbi::AssignDescriptors(
      &descriptor_table_camel_5fgrpc_2eproto_getter, &descriptor_table_camel_5fgrpc_2eproto_once,
      file_level_metadata_camel_5fgrpc_2eproto[0]);
}

// ===================================================================

class Token::_Internal {
 public:
  static const ::camel::api::Result& result(const Token* msg);
};

const ::camel::api::Result&
Token::_Internal::result(const Token* msg) {
  return *msg->_impl_.result_;
}
Token::Token(::PROTOBUF_NAMESPACE_ID::Arena* arena,
                         bool is_message_owned)
  : ::PROTOBUF_NAMESPACE_ID::Message(arena, is_message_owned) {
  SharedCtor(arena, is_message_owned);
  // @@protoc_insertion_point(arena_constructor:camel.api.Token)
}
Token::Token(const Token& from)
  : ::PROTOBUF_NAMESPACE_ID::Message() {
  Token* const _this = this; (void)_this;
  new (&_impl_) Impl_{
      decltype(_impl_.key_){}
    , decltype(_impl_.result_){nullptr}
    , /*decltype(_impl_._cached_size_)*/{}};

  _internal_metadata_.MergeFrom<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(from._internal_metadata_);
  _impl_.key_.InitDefault();
  #ifdef PROTOBUF_FORCE_COPY_DEFAULT_STRING
    _impl_.key_.Set("", GetArenaForAllocation());
  #endif // PROTOBUF_FORCE_COPY_DEFAULT_STRING
  if (!from._internal_key().empty()) {
    _this->_impl_.key_.Set(from._internal_key(), 
      _this->GetArenaForAllocation());
  }
  if (from._internal_has_result()) {
    _this->_impl_.result_ = new ::camel::api::Result(*from._impl_.result_);
  }
  // @@protoc_insertion_point(copy_constructor:camel.api.Token)
}

inline void Token::SharedCtor(
    ::_pb::Arena* arena, bool is_message_owned) {
  (void)arena;
  (void)is_message_owned;
  new (&_impl_) Impl_{
      decltype(_impl_.key_){}
    , decltype(_impl_.result_){nullptr}
    , /*decltype(_impl_._cached_size_)*/{}
  };
  _impl_.key_.InitDefault();
  #ifdef PROTOBUF_FORCE_COPY_DEFAULT_STRING
    _impl_.key_.Set("", GetArenaForAllocation());
  #endif // PROTOBUF_FORCE_COPY_DEFAULT_STRING
}

Token::~Token() {
  // @@protoc_insertion_point(destructor:camel.api.Token)
  if (auto *arena = _internal_metadata_.DeleteReturnArena<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>()) {
  (void)arena;
    return;
  }
  SharedDtor();
}

inline void Token::SharedDtor() {
  GOOGLE_DCHECK(GetArenaForAllocation() == nullptr);
  _impl_.key_.Destroy();
  if (this != internal_default_instance()) delete _impl_.result_;
}

void Token::SetCachedSize(int size) const {
  _impl_._cached_size_.Set(size);
}

void Token::Clear() {
// @@protoc_insertion_point(message_clear_start:camel.api.Token)
  uint32_t cached_has_bits = 0;
  // Prevent compiler warnings about cached_has_bits being unused
  (void) cached_has_bits;

  _impl_.key_.ClearToEmpty();
  if (GetArenaForAllocation() == nullptr && _impl_.result_ != nullptr) {
    delete _impl_.result_;
  }
  _impl_.result_ = nullptr;
  _internal_metadata_.Clear<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>();
}

const char* Token::_InternalParse(const char* ptr, ::_pbi::ParseContext* ctx) {
#define CHK_(x) if (PROTOBUF_PREDICT_FALSE(!(x))) goto failure
  while (!ctx->Done(&ptr)) {
    uint32_t tag;
    ptr = ::_pbi::ReadTag(ptr, &tag);
    switch (tag >> 3) {
      // string key = 1;
      case 1:
        if (PROTOBUF_PREDICT_TRUE(static_cast<uint8_t>(tag) == 10)) {
          auto str = _internal_mutable_key();
          ptr = ::_pbi::InlineGreedyStringParser(str, ptr, ctx);
          CHK_(ptr);
          CHK_(::_pbi::VerifyUTF8(str, "camel.api.Token.key"));
        } else
          goto handle_unusual;
        continue;
      // .camel.api.Result result = 2;
      case 2:
        if (PROTOBUF_PREDICT_TRUE(static_cast<uint8_t>(tag) == 18)) {
          ptr = ctx->ParseMessage(_internal_mutable_result(), ptr);
          CHK_(ptr);
        } else
          goto handle_unusual;
        continue;
      default:
        goto handle_unusual;
    }  // switch
  handle_unusual:
    if ((tag == 0) || ((tag & 7) == 4)) {
      CHK_(ptr);
      ctx->SetLastTag(tag);
      goto message_done;
    }
    ptr = UnknownFieldParse(
        tag,
        _internal_metadata_.mutable_unknown_fields<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(),
        ptr, ctx);
    CHK_(ptr != nullptr);
  }  // while
message_done:
  return ptr;
failure:
  ptr = nullptr;
  goto message_done;
#undef CHK_
}

uint8_t* Token::_InternalSerialize(
    uint8_t* target, ::PROTOBUF_NAMESPACE_ID::io::EpsCopyOutputStream* stream) const {
  // @@protoc_insertion_point(serialize_to_array_start:camel.api.Token)
  uint32_t cached_has_bits = 0;
  (void) cached_has_bits;

  // string key = 1;
  if (!this->_internal_key().empty()) {
    ::PROTOBUF_NAMESPACE_ID::internal::WireFormatLite::VerifyUtf8String(
      this->_internal_key().data(), static_cast<int>(this->_internal_key().length()),
      ::PROTOBUF_NAMESPACE_ID::internal::WireFormatLite::SERIALIZE,
      "camel.api.Token.key");
    target = stream->WriteStringMaybeAliased(
        1, this->_internal_key(), target);
  }

  // .camel.api.Result result = 2;
  if (this->_internal_has_result()) {
    target = ::PROTOBUF_NAMESPACE_ID::internal::WireFormatLite::
      InternalWriteMessage(2, _Internal::result(this),
        _Internal::result(this).GetCachedSize(), target, stream);
  }

  if (PROTOBUF_PREDICT_FALSE(_internal_metadata_.have_unknown_fields())) {
    target = ::_pbi::WireFormat::InternalSerializeUnknownFieldsToArray(
        _internal_metadata_.unknown_fields<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(::PROTOBUF_NAMESPACE_ID::UnknownFieldSet::default_instance), target, stream);
  }
  // @@protoc_insertion_point(serialize_to_array_end:camel.api.Token)
  return target;
}

size_t Token::ByteSizeLong() const {
// @@protoc_insertion_point(message_byte_size_start:camel.api.Token)
  size_t total_size = 0;

  uint32_t cached_has_bits = 0;
  // Prevent compiler warnings about cached_has_bits being unused
  (void) cached_has_bits;

  // string key = 1;
  if (!this->_internal_key().empty()) {
    total_size += 1 +
      ::PROTOBUF_NAMESPACE_ID::internal::WireFormatLite::StringSize(
        this->_internal_key());
  }

  // .camel.api.Result result = 2;
  if (this->_internal_has_result()) {
    total_size += 1 +
      ::PROTOBUF_NAMESPACE_ID::internal::WireFormatLite::MessageSize(
        *_impl_.result_);
  }

  return MaybeComputeUnknownFieldsSize(total_size, &_impl_._cached_size_);
}

const ::PROTOBUF_NAMESPACE_ID::Message::ClassData Token::_class_data_ = {
    ::PROTOBUF_NAMESPACE_ID::Message::CopyWithSourceCheck,
    Token::MergeImpl
};
const ::PROTOBUF_NAMESPACE_ID::Message::ClassData*Token::GetClassData() const { return &_class_data_; }


void Token::MergeImpl(::PROTOBUF_NAMESPACE_ID::Message& to_msg, const ::PROTOBUF_NAMESPACE_ID::Message& from_msg) {
  auto* const _this = static_cast<Token*>(&to_msg);
  auto& from = static_cast<const Token&>(from_msg);
  // @@protoc_insertion_point(class_specific_merge_from_start:camel.api.Token)
  GOOGLE_DCHECK_NE(&from, _this);
  uint32_t cached_has_bits = 0;
  (void) cached_has_bits;

  if (!from._internal_key().empty()) {
    _this->_internal_set_key(from._internal_key());
  }
  if (from._internal_has_result()) {
    _this->_internal_mutable_result()->::camel::api::Result::MergeFrom(
        from._internal_result());
  }
  _this->_internal_metadata_.MergeFrom<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(from._internal_metadata_);
}

void Token::CopyFrom(const Token& from) {
// @@protoc_insertion_point(class_specific_copy_from_start:camel.api.Token)
  if (&from == this) return;
  Clear();
  MergeFrom(from);
}

bool Token::IsInitialized() const {
  return true;
}

void Token::InternalSwap(Token* other) {
  using std::swap;
  auto* lhs_arena = GetArenaForAllocation();
  auto* rhs_arena = other->GetArenaForAllocation();
  _internal_metadata_.InternalSwap(&other->_internal_metadata_);
  ::PROTOBUF_NAMESPACE_ID::internal::ArenaStringPtr::InternalSwap(
      &_impl_.key_, lhs_arena,
      &other->_impl_.key_, rhs_arena
  );
  swap(_impl_.result_, other->_impl_.result_);
}

::PROTOBUF_NAMESPACE_ID::Metadata Token::GetMetadata() const {
  return ::_pbi::AssignDescriptors(
      &descriptor_table_camel_5fgrpc_2eproto_getter, &descriptor_table_camel_5fgrpc_2eproto_once,
      file_level_metadata_camel_5fgrpc_2eproto[1]);
}

// ===================================================================

class Result::_Internal {
 public:
};

Result::Result(::PROTOBUF_NAMESPACE_ID::Arena* arena,
                         bool is_message_owned)
  : ::PROTOBUF_NAMESPACE_ID::Message(arena, is_message_owned) {
  SharedCtor(arena, is_message_owned);
  // @@protoc_insertion_point(arena_constructor:camel.api.Result)
}
Result::Result(const Result& from)
  : ::PROTOBUF_NAMESPACE_ID::Message() {
  Result* const _this = this; (void)_this;
  new (&_impl_) Impl_{
      decltype(_impl_.message_){}
    , decltype(_impl_.errorcode_){}
    , /*decltype(_impl_._cached_size_)*/{}};

  _internal_metadata_.MergeFrom<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(from._internal_metadata_);
  _impl_.message_.InitDefault();
  #ifdef PROTOBUF_FORCE_COPY_DEFAULT_STRING
    _impl_.message_.Set("", GetArenaForAllocation());
  #endif // PROTOBUF_FORCE_COPY_DEFAULT_STRING
  if (!from._internal_message().empty()) {
    _this->_impl_.message_.Set(from._internal_message(), 
      _this->GetArenaForAllocation());
  }
  _this->_impl_.errorcode_ = from._impl_.errorcode_;
  // @@protoc_insertion_point(copy_constructor:camel.api.Result)
}

inline void Result::SharedCtor(
    ::_pb::Arena* arena, bool is_message_owned) {
  (void)arena;
  (void)is_message_owned;
  new (&_impl_) Impl_{
      decltype(_impl_.message_){}
    , decltype(_impl_.errorcode_){0}
    , /*decltype(_impl_._cached_size_)*/{}
  };
  _impl_.message_.InitDefault();
  #ifdef PROTOBUF_FORCE_COPY_DEFAULT_STRING
    _impl_.message_.Set("", GetArenaForAllocation());
  #endif // PROTOBUF_FORCE_COPY_DEFAULT_STRING
}

Result::~Result() {
  // @@protoc_insertion_point(destructor:camel.api.Result)
  if (auto *arena = _internal_metadata_.DeleteReturnArena<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>()) {
  (void)arena;
    return;
  }
  SharedDtor();
}

inline void Result::SharedDtor() {
  GOOGLE_DCHECK(GetArenaForAllocation() == nullptr);
  _impl_.message_.Destroy();
}

void Result::SetCachedSize(int size) const {
  _impl_._cached_size_.Set(size);
}

void Result::Clear() {
// @@protoc_insertion_point(message_clear_start:camel.api.Result)
  uint32_t cached_has_bits = 0;
  // Prevent compiler warnings about cached_has_bits being unused
  (void) cached_has_bits;

  _impl_.message_.ClearToEmpty();
  _impl_.errorcode_ = 0;
  _internal_metadata_.Clear<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>();
}

const char* Result::_InternalParse(const char* ptr, ::_pbi::ParseContext* ctx) {
#define CHK_(x) if (PROTOBUF_PREDICT_FALSE(!(x))) goto failure
  while (!ctx->Done(&ptr)) {
    uint32_t tag;
    ptr = ::_pbi::ReadTag(ptr, &tag);
    switch (tag >> 3) {
      // int32 errorCode = 1;
      case 1:
        if (PROTOBUF_PREDICT_TRUE(static_cast<uint8_t>(tag) == 8)) {
          _impl_.errorcode_ = ::PROTOBUF_NAMESPACE_ID::internal::ReadVarint32(&ptr);
          CHK_(ptr);
        } else
          goto handle_unusual;
        continue;
      // bytes message = 2;
      case 2:
        if (PROTOBUF_PREDICT_TRUE(static_cast<uint8_t>(tag) == 18)) {
          auto str = _internal_mutable_message();
          ptr = ::_pbi::InlineGreedyStringParser(str, ptr, ctx);
          CHK_(ptr);
        } else
          goto handle_unusual;
        continue;
      default:
        goto handle_unusual;
    }  // switch
  handle_unusual:
    if ((tag == 0) || ((tag & 7) == 4)) {
      CHK_(ptr);
      ctx->SetLastTag(tag);
      goto message_done;
    }
    ptr = UnknownFieldParse(
        tag,
        _internal_metadata_.mutable_unknown_fields<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(),
        ptr, ctx);
    CHK_(ptr != nullptr);
  }  // while
message_done:
  return ptr;
failure:
  ptr = nullptr;
  goto message_done;
#undef CHK_
}

uint8_t* Result::_InternalSerialize(
    uint8_t* target, ::PROTOBUF_NAMESPACE_ID::io::EpsCopyOutputStream* stream) const {
  // @@protoc_insertion_point(serialize_to_array_start:camel.api.Result)
  uint32_t cached_has_bits = 0;
  (void) cached_has_bits;

  // int32 errorCode = 1;
  if (this->_internal_errorcode() != 0) {
    target = stream->EnsureSpace(target);
    target = ::_pbi::WireFormatLite::WriteInt32ToArray(1, this->_internal_errorcode(), target);
  }

  // bytes message = 2;
  if (!this->_internal_message().empty()) {
    target = stream->WriteBytesMaybeAliased(
        2, this->_internal_message(), target);
  }

  if (PROTOBUF_PREDICT_FALSE(_internal_metadata_.have_unknown_fields())) {
    target = ::_pbi::WireFormat::InternalSerializeUnknownFieldsToArray(
        _internal_metadata_.unknown_fields<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(::PROTOBUF_NAMESPACE_ID::UnknownFieldSet::default_instance), target, stream);
  }
  // @@protoc_insertion_point(serialize_to_array_end:camel.api.Result)
  return target;
}

size_t Result::ByteSizeLong() const {
// @@protoc_insertion_point(message_byte_size_start:camel.api.Result)
  size_t total_size = 0;

  uint32_t cached_has_bits = 0;
  // Prevent compiler warnings about cached_has_bits being unused
  (void) cached_has_bits;

  // bytes message = 2;
  if (!this->_internal_message().empty()) {
    total_size += 1 +
      ::PROTOBUF_NAMESPACE_ID::internal::WireFormatLite::BytesSize(
        this->_internal_message());
  }

  // int32 errorCode = 1;
  if (this->_internal_errorcode() != 0) {
    total_size += ::_pbi::WireFormatLite::Int32SizePlusOne(this->_internal_errorcode());
  }

  return MaybeComputeUnknownFieldsSize(total_size, &_impl_._cached_size_);
}

const ::PROTOBUF_NAMESPACE_ID::Message::ClassData Result::_class_data_ = {
    ::PROTOBUF_NAMESPACE_ID::Message::CopyWithSourceCheck,
    Result::MergeImpl
};
const ::PROTOBUF_NAMESPACE_ID::Message::ClassData*Result::GetClassData() const { return &_class_data_; }


void Result::MergeImpl(::PROTOBUF_NAMESPACE_ID::Message& to_msg, const ::PROTOBUF_NAMESPACE_ID::Message& from_msg) {
  auto* const _this = static_cast<Result*>(&to_msg);
  auto& from = static_cast<const Result&>(from_msg);
  // @@protoc_insertion_point(class_specific_merge_from_start:camel.api.Result)
  GOOGLE_DCHECK_NE(&from, _this);
  uint32_t cached_has_bits = 0;
  (void) cached_has_bits;

  if (!from._internal_message().empty()) {
    _this->_internal_set_message(from._internal_message());
  }
  if (from._internal_errorcode() != 0) {
    _this->_internal_set_errorcode(from._internal_errorcode());
  }
  _this->_internal_metadata_.MergeFrom<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(from._internal_metadata_);
}

void Result::CopyFrom(const Result& from) {
// @@protoc_insertion_point(class_specific_copy_from_start:camel.api.Result)
  if (&from == this) return;
  Clear();
  MergeFrom(from);
}

bool Result::IsInitialized() const {
  return true;
}

void Result::InternalSwap(Result* other) {
  using std::swap;
  auto* lhs_arena = GetArenaForAllocation();
  auto* rhs_arena = other->GetArenaForAllocation();
  _internal_metadata_.InternalSwap(&other->_internal_metadata_);
  ::PROTOBUF_NAMESPACE_ID::internal::ArenaStringPtr::InternalSwap(
      &_impl_.message_, lhs_arena,
      &other->_impl_.message_, rhs_arena
  );
  swap(_impl_.errorcode_, other->_impl_.errorcode_);
}

::PROTOBUF_NAMESPACE_ID::Metadata Result::GetMetadata() const {
  return ::_pbi::AssignDescriptors(
      &descriptor_table_camel_5fgrpc_2eproto_getter, &descriptor_table_camel_5fgrpc_2eproto_once,
      file_level_metadata_camel_5fgrpc_2eproto[2]);
}

// @@protoc_insertion_point(namespace_scope)
}  // namespace api
}  // namespace camel
PROTOBUF_NAMESPACE_OPEN
template<> PROTOBUF_NOINLINE ::camel::api::GamepadControl*
Arena::CreateMaybeMessage< ::camel::api::GamepadControl >(Arena* arena) {
  return Arena::CreateMessageInternal< ::camel::api::GamepadControl >(arena);
}
template<> PROTOBUF_NOINLINE ::camel::api::Token*
Arena::CreateMaybeMessage< ::camel::api::Token >(Arena* arena) {
  return Arena::CreateMessageInternal< ::camel::api::Token >(arena);
}
template<> PROTOBUF_NOINLINE ::camel::api::Result*
Arena::CreateMaybeMessage< ::camel::api::Result >(Arena* arena) {
  return Arena::CreateMessageInternal< ::camel::api::Result >(arena);
}
PROTOBUF_NAMESPACE_CLOSE

// @@protoc_insertion_point(global_scope)
#include <google/protobuf/port_undef.inc>